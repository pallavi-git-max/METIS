import logging
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import desc, and_, or_
from datetime import datetime
from backend.models.project_request import ProjectRequest, StatusEnum, PriorityEnum
from backend.models.approval import Approval
from backend.models.user import User, RoleEnum
from backend.app import db
from backend.utils.validation import validate_approval_data
from backend.middleware.audit_middleware import log_user_action

approvals_bp = Blueprint('approvals', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    """Decorator to require faculty role (faculty, lab_incharge, hod)"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_faculty:
            return jsonify({
                'success': False,
                'message': 'Faculty access required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@approvals_bp.route('/pending', methods=['GET'])
@login_required
def pending_requests():
    """Get pending requests based on user role"""
    try:
        # Determine which requests the user can see based on their role (RBAC)
        if current_user.is_admin:
            # Admin can see all requests (full access)
            query = ProjectRequest.query.filter(
                or_(
                    ProjectRequest.status == StatusEnum.pending,
                    ProjectRequest.status == StatusEnum.lab_incharge_approved,
                    ProjectRequest.status == StatusEnum.faculty_approved,
                    ProjectRequest.status == StatusEnum.hod_approved,
                    ProjectRequest.status == StatusEnum.approved,
                    ProjectRequest.status == StatusEnum.rejected
                )
            )
        elif current_user.role == RoleEnum.lab_incharge:
            # Lab In-charge can see pending requests (first in workflow)
            query = ProjectRequest.query.filter_by(status=StatusEnum.pending)
        elif current_user.role == RoleEnum.faculty:
            # Faculty can see lab in-charge approved requests (second in workflow)
            query = ProjectRequest.query.filter_by(status=StatusEnum.lab_incharge_approved)
        elif current_user.role == RoleEnum.hod:
            # HoD can see faculty approved requests (third in workflow)
            query = ProjectRequest.query.filter_by(status=StatusEnum.faculty_approved)
        else:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions - Faculty/Admin access required'
            }), 403

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        priority_filter = request.args.get('priority')
        search = request.args.get('search')

        # Apply filters
        if priority_filter:
            query = query.filter(ProjectRequest.priority == priority_filter)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ProjectRequest.project_title.ilike(search_term),
                    ProjectRequest.description.ilike(search_term)
                )
            )

        # Paginate results
        requests = query.order_by(desc(ProjectRequest.submitted_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'requests': [req.to_dict() for req in requests.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': requests.total,
                    'pages': requests.pages,
                    'has_next': requests.has_next,
                    'has_prev': requests.has_prev
                }
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving pending requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve pending requests'
        }), 500

@approvals_bp.route('/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    """Approve a request based on user role"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        data = request.get_json() or {}
        
        # Check if request can be approved by current user
        can_approve, message = check_approval_permissions(request_obj, current_user)
        if not can_approve:
            return jsonify({
                'success': False,
                'message': message
            }), 403

        # Approve the request based on user role (Lab In-charge → Faculty → HOD → Admin)
        if current_user.role == RoleEnum.lab_incharge:
            request_obj.approve_by_role('lab_incharge')
        elif current_user.role == RoleEnum.faculty:
            request_obj.approve_by_role('faculty')
        elif current_user.role == RoleEnum.hod:
            request_obj.approve_by_role('hod')
        elif current_user.is_admin:
            request_obj.approve_by_role('admin')

        # Create approval record
        approval = Approval(
            project_request_id=request_id,
            admin_id=current_user.id,
            approved=True,
            comments=data.get('comments', '')
        )
        
        db.session.add(approval)
        db.session.commit()

        # Send email notification if request is fully approved
        if request_obj.status == StatusEnum.approved:
            try:
                from backend.services.email_service import EmailService
                email_service = EmailService()
                email_service.send_approval_notification(request_obj, current_user)
            except Exception as e:
                logger.error(f"Failed to send approval notification: {str(e)}")

        # Log approval action
        log_user_action(
            action='approve',
            resource_type='project_request',
            resource_id=request_id,
            details={
                'approved_by_role': current_user.role.value,
                'new_status': request_obj.status.value,
                'comments': data.get('comments', '')
            }
        )

        logger.info(f"Request {request_id} approved by {current_user.role.value} {current_user.id}")

        return jsonify({
            'success': True,
            'message': 'Request approved successfully',
            'data': request_obj.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error approving request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to approve request'
        }), 500

@approvals_bp.route('/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    """Reject a request"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        if not data or 'reason' not in data:
            return jsonify({
                'success': False,
                'message': 'Rejection reason is required'
            }), 400

        # Check if request can be rejected by current user
        can_reject, message = check_rejection_permissions(request_obj, current_user)
        if not can_reject:
            return jsonify({
                'success': False,
                'message': message
            }), 403

        # Reject the request
        request_obj.reject_request(data['reason'])

        # Create approval record
        approval = Approval(
            project_request_id=request_id,
            admin_id=current_user.id,
            approved=False,
            comments=data['reason']
        )
        
        db.session.add(approval)
        db.session.commit()

        # Send email notification for rejection
        try:
            from backend.services.email_service import EmailService
            email_service = EmailService()
            email_service.send_rejection_notification(request_obj, current_user, data['reason'])
        except Exception as e:
            logger.error(f"Failed to send rejection notification: {str(e)}")

        # Log rejection action
        log_user_action(
            action='reject',
            resource_type='project_request',
            resource_id=request_id,
            details={
                'rejected_by_role': current_user.role.value,
                'reason': data['reason']
            }
        )

        logger.info(f"Request {request_id} rejected by {current_user.role.value} {current_user.id}")

        return jsonify({
            'success': True,
            'message': 'Request rejected successfully',
            'data': request_obj.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error rejecting request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to reject request'
        }), 500

@approvals_bp.route('/<int:request_id>/details', methods=['GET'])
@login_required
def request_details(request_id):
    """Get detailed information about a request for approval"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        
        # Check if user can view this request
        can_view, message = check_view_permissions(request_obj, current_user)
        if not can_view:
            return jsonify({
                'success': False,
                'message': message
            }), 403

        # Get approval history
        approvals = Approval.query.filter_by(project_request_id=request_id).all()
        
        # Get user information
        user = User.query.get(request_obj.user_id)

        return jsonify({
            'success': True,
            'data': {
                'request': request_obj.to_dict(),
                'user': user.to_dict() if user else None,
                'approvals': [{
                    'id': approval.id,
                    'admin_name': approval.admin.full_name if approval.admin else 'Unknown',
                    'admin_role': approval.admin.role.value if approval.admin else 'Unknown',
                    'approved': approval.approved,
                    'comments': approval.comments,
                    'timestamp': approval.timestamp.isoformat()
                } for approval in approvals]
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving request details {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve request details'
        }), 500

@approvals_bp.route('/queue', methods=['GET'])
@login_required
def approval_queue():
    """Get approval queue for the current user"""
    try:
        # Get requests that need action from current user (Lab In-charge → Faculty → HOD → Admin)
        if current_user.role == RoleEnum.lab_incharge:
            query = ProjectRequest.query.filter_by(status=StatusEnum.pending)
        elif current_user.role == RoleEnum.faculty:
            query = ProjectRequest.query.filter_by(status=StatusEnum.lab_incharge_approved)
        elif current_user.role == RoleEnum.hod:
            query = ProjectRequest.query.filter_by(status=StatusEnum.faculty_approved)
        elif current_user.is_admin:
            query = ProjectRequest.query.filter_by(status=StatusEnum.hod_approved)
        else:
            return jsonify({
                'success': False,
                'message': 'No approval permissions'
            }), 403

        # Get recent requests (last 10)
        requests = query.order_by(desc(ProjectRequest.submitted_at)).limit(10).all()

        return jsonify({
            'success': True,
            'data': {
                'queue': [req.to_dict() for req in requests],
                'queue_count': len(requests)
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving approval queue: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve approval queue'
        }), 500

@approvals_bp.route('/statistics', methods=['GET'])
@login_required
def approval_statistics():
    """Get approval statistics for faculty users"""
    try:
        if not current_user.is_faculty and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Faculty access required'
            }), 403

        # Get statistics based on user role
        if current_user.role == RoleEnum.hod:
            pending_count = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
            processed_count = ProjectRequest.query.filter_by(status=StatusEnum.hod_submitted).count()
        elif current_user.role == RoleEnum.faculty:
            pending_count = ProjectRequest.query.filter_by(status=StatusEnum.hod_submitted).count()
            processed_count = ProjectRequest.query.filter_by(status=StatusEnum.faculty_approved).count()
        elif current_user.role == RoleEnum.lab_incharge:
            pending_count = ProjectRequest.query.filter_by(status=StatusEnum.faculty_approved).count()
            processed_count = ProjectRequest.query.filter_by(status=StatusEnum.lab_incharge_approved).count()
        else:  # admin
            pending_count = ProjectRequest.query.filter_by(status=StatusEnum.lab_incharge_approved).count()
            processed_count = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()

        # Get approval history for current user
        user_approvals = Approval.query.filter_by(admin_id=current_user.id).all()
        approved_count = len([a for a in user_approvals if a.approved])
        rejected_count = len([a for a in user_approvals if not a.approved])

        statistics = {
            'pending_count': pending_count,
            'processed_count': processed_count,
            'user_approvals': {
                'approved': approved_count,
                'rejected': rejected_count,
                'total': len(user_approvals)
            },
            'approval_rate': round((approved_count / len(user_approvals) * 100), 2) if user_approvals else 0
        }

        return jsonify({
            'success': True,
            'data': statistics
        })

    except Exception as e:
        logger.error(f"Error retrieving approval statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve approval statistics'
        }), 500

def check_approval_permissions(request_obj, user):
    """Check if user can approve the request (Lab In-charge → Faculty → HOD → Admin)"""
    if user.is_admin:
        return True, "Admin can approve any request"
    
    if user.role == RoleEnum.lab_incharge and request_obj.status == StatusEnum.pending:
        return True, "Lab In-charge can approve pending requests"
    
    if user.role == RoleEnum.faculty and request_obj.status == StatusEnum.lab_incharge_approved:
        return True, "Faculty can approve lab in-charge approved requests"
    
    if user.role == RoleEnum.hod and request_obj.status == StatusEnum.faculty_approved:
        return True, "HoD can approve faculty approved requests"
    
    return False, "Insufficient permissions to approve this request at current stage"

def check_rejection_permissions(request_obj, user):
    """Check if user can reject the request"""
    # Any faculty member or admin can reject requests
    if user.is_faculty or user.is_admin:
        return True, "Faculty/Admin can reject requests"
    
    return False, "Insufficient permissions to reject this request"

def check_view_permissions(request_obj, user):
    """Check if user can view the request details"""
    # Users can view their own requests
    if request_obj.user_id == user.id:
        return True, "User can view their own requests"
    
    # Faculty and admin can view all requests
    if user.is_faculty or user.is_admin:
        return True, "Faculty/Admin can view all requests"
    
    return False, "Insufficient permissions to view this request"