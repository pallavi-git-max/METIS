from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_, func
from datetime import datetime
import logging
from backend.models.project_request import ProjectRequest, StatusEnum, PriorityEnum
from backend.models.approval import Approval
from backend.models.user import User
from backend.models import db
from backend.utils.validation import validate_approval_data

request_bp = Blueprint('admin_requests', __name__)

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            return jsonify({
                'message': 'Access forbidden. Admin privileges required.'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@request_bp.route('/requests', methods=['GET'])
@login_required
@admin_required
def get_requests():
    """Get all project requests with filtering and pagination"""
    try:
        from sqlalchemy.orm import joinedload
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        search = request.args.get('search')
        
        # Build query with eager loading
        query = ProjectRequest.query.options(joinedload(ProjectRequest.user))
        
        if status_filter:
            # Accept plain string status value
            try:
                query = query.filter(ProjectRequest.status == StatusEnum(status_filter))
            except Exception:
                query = query.filter(ProjectRequest.status == status_filter)
        
        if priority_filter:
            query = query.filter(ProjectRequest.priority == priority_filter)
        if search:
            try:
                # Try to convert to integer for ID search
                request_id = int(search)
                query = query.filter(ProjectRequest.id == request_id)
            except ValueError:
                # If not a valid integer, search by title/description/purpose
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        ProjectRequest.project_title.ilike(search_term),
                        ProjectRequest.description.ilike(search_term),
                        ProjectRequest.purpose.ilike(search_term)
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
        logger.error(f"Error retrieving requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve requests'
        }), 500

@request_bp.route('/requests/rejected', methods=['GET'])
@login_required
def get_rejected_requests():
    """List recently rejected requests with who rejected and reason."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        date_range = request.args.get('date_range')  # today | week | month
        search = request.args.get('search')

        base_query = ProjectRequest.query.filter(ProjectRequest.status == StatusEnum.rejected)

        # Build subquery to get latest rejection Approval per request
        latest_rej_subq = (
            db.session.query(
                Approval.project_request_id.label('req_id'),
                func.max(Approval.timestamp).label('max_ts')
            )
            .filter(Approval.approved.is_(False))
            .group_by(Approval.project_request_id)
            .subquery()
        )

        # Join to get Approval and User info
        joined = (
            db.session.query(ProjectRequest, Approval, User)
            .join(latest_rej_subq, latest_rej_subq.c.req_id == ProjectRequest.id)
            .join(Approval, (Approval.project_request_id == ProjectRequest.id) & (Approval.timestamp == latest_rej_subq.c.max_ts))
            .join(User, User.id == Approval.admin_id)
            .filter(ProjectRequest.status == StatusEnum.rejected)
            .order_by(desc(ProjectRequest.rejected_at))
        )

        # Apply date range filter
        if date_range:
            now = datetime.utcnow()
            start_dt = None
            if date_range == 'today':
                start_dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_range == 'week':
                from datetime import timedelta
                start_dt = now - timedelta(days=7)
            elif date_range == 'month':
                from datetime import timedelta
                start_dt = now - timedelta(days=30)
            if start_dt:
                joined = joined.filter(ProjectRequest.rejected_at >= start_dt)

        # Apply search filter (title or user name)
        if search:
            like = f"%{search}%"
            joined = joined.filter(
                or_(
                    ProjectRequest.project_title.ilike(like),
                    ProjectRequest.purpose.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like)
                )
            )

        total = joined.count()
        items = joined.limit(per_page).offset((page - 1) * per_page).all()

        data_items = []
        for req, appr, user in items:
            item = req.to_dict()
            item.update({
                'rejected_by_id': user.id,
                'rejected_by_name': user.full_name,
                'rejection_comment': appr.comments,
                'rejection_logged_at': appr.timestamp.isoformat() if appr.timestamp else None
            })
            data_items.append(item)

        return jsonify({
            'success': True,
            'data': {
                'requests': data_items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': page * per_page < total,
                    'has_prev': page > 1
                }
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving rejected requests: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to retrieve rejected requests'}), 500

@request_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_request(request_id):
    """Approve a project request"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        data = request.get_json() or {}
        
        # Check if request can be approved
        if request_obj.status == StatusEnum.approved:
            return jsonify({
                'success': False,
                'message': 'Request is already approved'
            }), 400
        
        if request_obj.status == StatusEnum.rejected:
            return jsonify({
                'success': False,
                'message': 'Cannot approve a rejected request'
            }), 400
        
        # Approve the request
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
        
        logger.info(f"Request {request_id} approved by admin {current_user.id}")
        
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

@request_bp.route('/requests/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_request(request_id):
    """Reject a project request"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        if not data or 'reason' not in data:
            return jsonify({
                'success': False,
                'message': 'Rejection reason is required'
            }), 400
        
        # Check if request can be rejected
        if request_obj.status == StatusEnum.rejected:
            return jsonify({
                'success': False,
                'message': 'Request is already rejected'
            }), 400
        
        if request_obj.status == StatusEnum.approved:
            return jsonify({
                'success': False,
                'message': 'Cannot reject an approved request'
            }), 400
        
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
        
        logger.info(f"Request {request_id} rejected by admin {current_user.id}")
        
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

@request_bp.route('/requests/<int:request_id>', methods=['GET'])
@login_required
@admin_required
def get_request_details(request_id):
    """Get detailed information about a specific request"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        
        # Get approval history
        approvals = Approval.query.filter_by(project_request_id=request_id).all()
        
        return jsonify({
            'success': True,
            'data': {
                'request': request_obj.to_dict(),
                'approvals': [{
                    'id': approval.id,
                    'admin_name': approval.admin.full_name if approval.admin else 'Unknown',
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

@request_bp.route('/requests/<int:request_id>/status', methods=['PUT'])
@login_required
@admin_required
def update_request_status(request_id):
    """Update request status"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400
        
        # Validate status
        valid_statuses = [status.value for status in StatusEnum]
        if data['status'] not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Update status
        old_status = request_obj.status.value
        request_obj.status = StatusEnum(data['status'])
        request_obj.updated_at = datetime.utcnow()
        
        # Set appropriate timestamps
        now = datetime.utcnow()
        if data['status'] == 'approved':
            request_obj.approved_at = now
        elif data['status'] == 'rejected':
            request_obj.rejected_at = now
            request_obj.rejection_reason = data.get('reason', '')
        
        db.session.commit()
        
        logger.info(f"Request {request_id} status updated from {old_status} to {data['status']} by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request status updated successfully',
            'data': request_obj.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating request status {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update request status'
        }), 500

@request_bp.route('/requests/<int:request_id>/restore', methods=['POST'])
@login_required
def restore_request(request_id):
    """Restore a rejected request back to pending status"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        
        # Check if request is rejected
        if request_obj.status != StatusEnum.rejected:
            return jsonify({
                'success': False,
                'message': 'Only rejected requests can be restored'
            }), 400
        
        # Restore to pending status
        request_obj.status = StatusEnum.pending
        request_obj.rejected_at = None
        request_obj.rejection_reason = None
        request_obj.updated_at = datetime.utcnow()
        
        # Clear all approval timestamps to restart the workflow
        request_obj.guide_approved_at = None
        request_obj.hod_approved_at = None
        request_obj.it_services_approved_at = None
        request_obj.approved_at = None
        
        # Clear approval references
        request_obj.guide_approved_by = None
        request_obj.hod_approved_by = None
        request_obj.it_services_approved_by = None
        
        db.session.commit()
        
        logger.info(f"Request {request_id} restored to pending by admin {current_user.id}")
        return jsonify({
            'success': True,
            'message': 'Request restored successfully',
            'data': request_obj.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to restore request'
        }), 500