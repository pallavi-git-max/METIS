from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import desc
from datetime import datetime
import logging
from backend.models.user import User, RoleEnum
from backend.models.project_request import ProjectRequest, StatusEnum
from backend.models import db
from backend.utils.database_utils import safe_db_operation
from backend.services.email_service import EmailService

approvals_bp = Blueprint('approvals', __name__)

# Configure logging
logger = logging.getLogger(__name__)

def role_required(required_role):
    """Decorator to require specific role"""
    from functools import wraps
    @wraps(required_role)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
            # Check if user has the required role
            if current_user.role != required_role:
                logger.warning(f"Unauthorized access attempt by user {current_user.id} with role {current_user.role}")
                return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@approvals_bp.route('/guide/dashboard', methods=['GET'])
@login_required
@role_required(RoleEnum.project_guide)
def guide_dashboard():
    """Get requests pending guide approval"""
    try:
        # Get requests that need guide approval (pending status)
        def get_pending_requests():
            return ProjectRequest.query.filter_by(status=StatusEnum.pending).order_by(desc(ProjectRequest.submitted_at)).all()
        
        requests = safe_db_operation(get_pending_requests)
        
        # Get guide's own approved requests
        def get_guide_approved():
            return ProjectRequest.query.filter_by(
                status=StatusEnum.guide_approved,
                guide_approved_by=current_user.id
            ).order_by(desc(ProjectRequest.guide_approved_at)).all()
        
        guide_approved = safe_db_operation(get_guide_approved)
        
        # Get overall statistics
        total_users = User.query.count()
        total_requests = ProjectRequest.query.count()
        pending_requests_overall = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
        approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()
        students_count = User.query.filter_by(role=RoleEnum.student).count()
        
        return jsonify({
            'success': True,
            'data': {
                'pending_requests': [req.to_dict() for req in requests],
                'guide_approved': [req.to_dict() for req in guide_approved],
                'stats': {
                    'pending_count': len(requests),
                    'approved_count': len(guide_approved),
                    'students_count': students_count,
                    'total_requests': total_requests,
                    'pending_requests': pending_requests_overall,
                    'approved_requests': approved_requests
                }
            }
        })
    except Exception as e:
        logger.error(f"Error in guide dashboard: {e}")
        return jsonify({'success': False, 'message': 'Failed to load guide dashboard'}), 500

@approvals_bp.route('/guide/approve/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.project_guide)
def guide_approve(request_id):
    """Guide approves a request"""
    try:
        def approve_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            if request_obj.status != StatusEnum.pending:
                raise ValueError("Request is not in pending status")
            
            request_obj.approve_by_role('guide', current_user.id)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(approve_request)
        
        # Send email notification to next approver (HOD)
        email_service = EmailService()
        email_service.send_stage_approval_notification(request_obj, current_user, 'guide')
        
        logger.info(f"Request {request_id} approved by guide {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request approved successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error approving request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/guide/reject/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.project_guide)
def guide_reject(request_id):
    """Guide rejects a request"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        def reject_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            if request_obj.status != StatusEnum.pending:
                raise ValueError("Request is not in pending status")
            
            request_obj.reject_request(reason)
            # Log rejection for audit/attribution
            from backend.models.approval import Approval
            approval = Approval(
                project_request_id=request_id,
                admin_id=current_user.id,
                approved=False,
                comments=reason
            )
            db.session.add(approval)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(reject_request)
        
        # Send email notification to user about rejection
        email_service = EmailService()
        email_service.send_stage_rejection_notification(request_obj, current_user, 'guide', reason)
        
        logger.info(f"Request {request_id} rejected by guide {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request rejected successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error rejecting request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/hod/dashboard', methods=['GET'])
@login_required
@role_required(RoleEnum.hod)
def hod_dashboard():
    """Get requests pending HOD approval"""
    try:
        # Get requests that need HOD approval
        # - guide_approved status (from students after guide approval)
        # - pending status from faculty/external users (who skip guide approval)
        def get_pending_requests():
            # Get guide-approved requests (from students)
            guide_approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.guide_approved).all()
            
            # Get pending requests from faculty/external users (who skip guide approval)
            faculty_pending_requests = ProjectRequest.query.join(ProjectRequest.user).filter(
                ProjectRequest.status == StatusEnum.pending,
                User.role.in_([RoleEnum.faculty, RoleEnum.external])
            ).all()
            
            # Combine both lists
            all_requests = guide_approved_requests + faculty_pending_requests
            
            # Sort by submission time (most recent first)
            all_requests.sort(key=lambda x: x.submitted_at, reverse=True)
            
            return all_requests
        
        requests = safe_db_operation(get_pending_requests)
        
        # Get HOD's own approved requests
        def get_hod_approved():
            return ProjectRequest.query.filter_by(
                status=StatusEnum.hod_approved,
                hod_approved_by=current_user.id
            ).order_by(desc(ProjectRequest.hod_approved_at)).all()
        
        hod_approved = safe_db_operation(get_hod_approved)
        
        # Get overall statistics
        total_users = User.query.count()
        total_requests = ProjectRequest.query.count()
        pending_requests_overall = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
        approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()
        students_count = User.query.filter_by(role=RoleEnum.student).count()
        
        return jsonify({
            'success': True,
            'data': {
                'pending_requests': [req.to_dict() for req in requests],
                'hod_approved': [req.to_dict() for req in hod_approved],
                'stats': {
                    'pending_count': len(requests),
                    'approved_count': len(hod_approved),
                    'students_count': students_count,
                    'total_requests': total_requests,
                    'pending_requests': pending_requests_overall,
                    'approved_requests': approved_requests
                }
            }
        })
    except Exception as e:
        logger.error(f"Error in HOD dashboard: {e}")
        return jsonify({'success': False, 'message': 'Failed to load HOD dashboard'}), 500

@approvals_bp.route('/hod/approve/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.hod)
def hod_approve(request_id):
    """HOD approves a request"""
    try:
        def approve_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            # Check if user is student (requires guide approval) or faculty/external (skip guide approval)
            user = request_obj.user
            is_student = user.role == RoleEnum.student
            
            if is_student:
                # Students must have guide approval before HOD can approve
                if request_obj.status != StatusEnum.guide_approved:
                    raise ValueError("Student requests must be approved by guide before HOD approval")
            else:
                # Faculty/External users skip guide approval
                if request_obj.status != StatusEnum.pending:
                    raise ValueError("Faculty/External requests must be in pending status for HOD approval")
            
            request_obj.approve_by_role('hod', current_user.id)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(approve_request)
        
        # Send email notification to next approver (IT Services)
        email_service = EmailService()
        email_service.send_stage_approval_notification(request_obj, current_user, 'hod')
        
        logger.info(f"Request {request_id} approved by HOD {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request approved successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error approving request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/hod/reject/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.hod)
def hod_reject(request_id):
    """HOD rejects a request"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        def reject_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            # Check if user is student (requires guide approval) or faculty/external (skip guide approval)
            user = request_obj.user
            is_student = user.role == RoleEnum.student
            
            if is_student:
                # Students must have guide approval before HOD can reject
                if request_obj.status != StatusEnum.guide_approved:
                    raise ValueError("Student requests must be approved by guide before HOD rejection")
            else:
                # Faculty/External users skip guide approval
                if request_obj.status != StatusEnum.pending:
                    raise ValueError("Faculty/External requests must be in pending status for HOD rejection")
            
            request_obj.reject_request(reason)
            from backend.models.approval import Approval
            approval = Approval(
                project_request_id=request_id,
                admin_id=current_user.id,
                approved=False,
                comments=reason
            )
            db.session.add(approval)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(reject_request)
        
        # Send email notification to user about rejection
        email_service = EmailService()
        email_service.send_stage_rejection_notification(request_obj, current_user, 'hod', reason)
        
        logger.info(f"Request {request_id} rejected by HOD {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request rejected successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error rejecting request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/it-services/dashboard', methods=['GET'])
@login_required
@role_required(RoleEnum.it_services)
def it_services_dashboard():
    """Get requests pending IT Services approval"""
    try:
        # Get requests that need IT Services approval (hod_approved status)
        def get_pending_requests():
            return ProjectRequest.query.filter_by(status=StatusEnum.hod_approved).order_by(desc(ProjectRequest.hod_approved_at)).all()
        
        requests = safe_db_operation(get_pending_requests)
        
        # Get IT Services' own approved requests
        def get_it_services_approved():
            return ProjectRequest.query.filter_by(
                status=StatusEnum.it_services_approved,
                it_services_approved_by=current_user.id
            ).order_by(desc(ProjectRequest.it_services_approved_at)).all()
        
        it_services_approved = safe_db_operation(get_it_services_approved)
        
        # Get overall statistics
        total_users = User.query.count()
        total_requests = ProjectRequest.query.count()
        pending_requests_overall = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
        approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()
        students_count = User.query.filter_by(role=RoleEnum.student).count()
        
        return jsonify({
            'success': True,
            'data': {
                'pending_requests': [req.to_dict() for req in requests],
                'it_services_approved': [req.to_dict() for req in it_services_approved],
                'stats': {
                    'pending_count': len(requests),
                    'approved_count': len(it_services_approved),
                    'students_count': students_count,
                    'total_requests': total_requests,
                    'pending_requests': pending_requests_overall,
                    'approved_requests': approved_requests
                }
            }
        })
    except Exception as e:
        logger.error(f"Error in IT Services dashboard: {e}")
        return jsonify({'success': False, 'message': 'Failed to load IT Services dashboard'}), 500

@approvals_bp.route('/it-services/approve/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.it_services)
def it_services_approve(request_id):
    """IT Services approves a request"""
    try:
        def approve_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            if request_obj.status != StatusEnum.hod_approved:
                raise ValueError("Request must be approved by HOD before IT Services approval")
            
            request_obj.approve_by_role('it_services', current_user.id)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(approve_request)
        
        # Send email notification to next approver (Admin)
        email_service = EmailService()
        email_service.send_stage_approval_notification(request_obj, current_user, 'it_services')
        
        logger.info(f"Request {request_id} approved by IT Services {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request approved successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error approving request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/it-services/reject/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.it_services)
def it_services_reject(request_id):
    """IT Services rejects a request"""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        def reject_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            if request_obj.status != StatusEnum.hod_approved:
                raise ValueError("Request must be approved by HOD before IT Services rejection")
            
            request_obj.reject_request(reason)
            from backend.models.approval import Approval
            approval = Approval(
                project_request_id=request_id,
                admin_id=current_user.id,
                approved=False,
                comments=reason
            )
            db.session.add(approval)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(reject_request)
        
        # Send email notification to user about rejection
        email_service = EmailService()
        email_service.send_stage_rejection_notification(request_obj, current_user, 'it_services', reason)
        
        logger.info(f"Request {request_id} rejected by IT Services {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request rejected successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error rejecting request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/admin/final-approve/<int:request_id>', methods=['POST'])
@login_required
@role_required(RoleEnum.admin)
def admin_final_approve(request_id):
    """Admin gives final approval to a request"""
    try:
        def approve_request():
            request_obj = ProjectRequest.query.get_or_404(request_id)
            
            if request_obj.status != StatusEnum.it_services_approved:
                raise ValueError("Request is not in IT Services approved status")
            
            request_obj.approve_by_role('admin', current_user.id)
            db.session.commit()
            return request_obj
        
        request_obj = safe_db_operation(approve_request)
        
        # Send final approval notification to user
        email_service = EmailService()
        email_service.send_approval_notification(request_obj, current_user)
        
        logger.info(f"Request {request_id} given final approval by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request approved successfully',
            'data': request_obj.to_dict()
        })
    except Exception as e:
        logger.error(f"Error approving request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400

@approvals_bp.route('/workflow/<int:request_id>', methods=['GET'])
@login_required
def get_workflow_status(request_id):
    """Get workflow status for a request"""
    try:
        def get_request():
            return ProjectRequest.query.get_or_404(request_id)
        
        request_obj = safe_db_operation(get_request)
        
        # Check if user is faculty/external (skip guide approval for them)
        user = request_obj.user
        skip_guide_approval = user.role in [RoleEnum.faculty, RoleEnum.external]
        
        # Determine workflow steps based on user role
        if skip_guide_approval:
            # Faculty/External workflow: Submitted → HOD → IT Services → Final Approval
            workflow_steps = [
                {'step': 'submitted', 'status': 'completed', 'timestamp': request_obj.submitted_at},
                {'step': 'hod_approval', 'status': 'pending', 'timestamp': None},
                {'step': 'it_services_approval', 'status': 'pending', 'timestamp': None},
                {'step': 'final_approval', 'status': 'pending', 'timestamp': None}
            ]
            
            # Update step statuses based on current status (no guide approval)
            # For faculty/external: pending -> waiting for HOD, hod_approved -> waiting for IT Services
            if request_obj.status in [StatusEnum.hod_approved, StatusEnum.it_services_approved, StatusEnum.approved]:
                workflow_steps[1]['status'] = 'completed'
                workflow_steps[1]['timestamp'] = request_obj.hod_approved_at
            elif request_obj.status == StatusEnum.pending:
                workflow_steps[1]['status'] = 'pending'  # Currently waiting for HOD
            
            if request_obj.status in [StatusEnum.it_services_approved, StatusEnum.approved]:
                workflow_steps[2]['status'] = 'completed'
                workflow_steps[2]['timestamp'] = request_obj.it_services_approved_at
            
            if request_obj.status == StatusEnum.approved:
                workflow_steps[3]['status'] = 'completed'
                workflow_steps[3]['timestamp'] = request_obj.approved_at
            
            if request_obj.status == StatusEnum.rejected:
                # Find which step was rejected
                if request_obj.hod_approved_at is None:
                    workflow_steps[1]['status'] = 'rejected'
                elif request_obj.it_services_approved_at is None:
                    workflow_steps[2]['status'] = 'rejected'
        else:
            # Student workflow: Submitted → Guide → HOD → IT Services → Final Approval
            workflow_steps = [
                {'step': 'submitted', 'status': 'completed', 'timestamp': request_obj.submitted_at},
                {'step': 'guide_approval', 'status': 'pending', 'timestamp': None},
                {'step': 'hod_approval', 'status': 'pending', 'timestamp': None},
                {'step': 'it_services_approval', 'status': 'pending', 'timestamp': None},
                {'step': 'final_approval', 'status': 'pending', 'timestamp': None}
            ]
            
            # Update step statuses based on current status
            if request_obj.status in [StatusEnum.guide_approved, StatusEnum.hod_approved, StatusEnum.it_services_approved, StatusEnum.approved]:
                workflow_steps[1]['status'] = 'completed'
                workflow_steps[1]['timestamp'] = request_obj.guide_approved_at
            
            if request_obj.status in [StatusEnum.hod_approved, StatusEnum.it_services_approved, StatusEnum.approved]:
                workflow_steps[2]['status'] = 'completed'
                workflow_steps[2]['timestamp'] = request_obj.hod_approved_at
            
            if request_obj.status in [StatusEnum.it_services_approved, StatusEnum.approved]:
                workflow_steps[3]['status'] = 'completed'
                workflow_steps[3]['timestamp'] = request_obj.it_services_approved_at
            
            if request_obj.status == StatusEnum.approved:
                workflow_steps[4]['status'] = 'completed'
                workflow_steps[4]['timestamp'] = request_obj.approved_at
            
            if request_obj.status == StatusEnum.rejected:
                # Find which step was rejected
                if request_obj.guide_approved_at is None:
                    workflow_steps[1]['status'] = 'rejected'
                elif request_obj.hod_approved_at is None:
                    workflow_steps[2]['status'] = 'rejected'
                elif request_obj.it_services_approved_at is None:
                    workflow_steps[3]['status'] = 'rejected'
        
        return jsonify({
            'success': True,
            'data': {
                'request': request_obj.to_dict(),
                'workflow': workflow_steps,
                'current_status': request_obj.status.value
            }
        })
    except Exception as e:
        logger.error(f"Error getting workflow status for request {request_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 400