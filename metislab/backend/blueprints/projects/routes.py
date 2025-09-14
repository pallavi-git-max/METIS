import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_
from datetime import datetime
from backend.models.project_request import ProjectRequest, StatusEnum, PriorityEnum
from backend.models.user import User
from backend.models.nda import NDA
from backend.app import db
from backend.utils.validation import validate_request_data
from backend.utils.error_handlers import ValidationError, BusinessLogicError
from backend.middleware.audit_middleware import log_user_action

projects_bp = Blueprint('projects', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@projects_bp.route('/', methods=['GET'])
@login_required
def list_requests():
    """Get all project requests for the current user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status')
        
        # Build query
        query = ProjectRequest.query.filter_by(user_id=current_user.id)
        
        if status_filter:
            query = query.filter(ProjectRequest.status == status_filter)
        
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
        logger.error(f"Error retrieving user requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve requests'
        }), 500

@projects_bp.route('/submit', methods=['POST'])
@login_required
def submit_request():
    """Submit a new project request with comprehensive form data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['project_title', 'description', 'purpose']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Check if user has approved NDA
        nda = NDA.query.filter_by(user_id=current_user.id).first()
        if not nda or not nda.is_approved:
            return jsonify({
                'success': False,
                'message': 'Approved NDA is required before submitting project requests'
            }), 400

        # Validate request data
        is_valid, message = validate_request_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # Create new project request with status=pending
        new_request = ProjectRequest(
            user_id=current_user.id,
            project_title=data['project_title'],
            description=data['description'],
            purpose=data['purpose'],
            expected_duration=data.get('expected_duration'),
            priority=PriorityEnum(data.get('priority', 'medium')),
            status=StatusEnum.pending,  # Always start with pending status
            submitted_at=datetime.utcnow()
        )

        # Add additional form data as JSON in description or create separate fields
        form_data = {
            'fields_of_interest': data.get('fields', []),
            'package_preference': data.get('package'),
            'dataset_status': data.get('dataset_status'),
            'dataset_size': data.get('dataset_size'),
            'data_types': data.get('data_type', []),
            'computational_requirements': data.get('cores'),
            'additional_requirements': data.get('additional_requirements', ''),
            'declaration_accepted': data.get('agree', False)
        }

        # Store additional form data in description (or create a separate JSON field)
        additional_info = f"\n\nAdditional Information:\n"
        additional_info += f"Fields of Interest: {', '.join(form_data['fields_of_interest'])}\n"
        additional_info += f"Package Preference: {form_data['package_preference']}\n"
        additional_info += f"Dataset Status: {form_data['dataset_status']}\n"
        additional_info += f"Dataset Size: {form_data['dataset_size']}\n"
        additional_info += f"Data Types: {', '.join(form_data['data_types'])}\n"
        additional_info += f"Computational Requirements: {form_data['computational_requirements']} cores\n"
        if form_data['additional_requirements']:
            additional_info += f"Additional Requirements: {form_data['additional_requirements']}\n"
        additional_info += f"Declaration Accepted: {form_data['declaration_accepted']}"

        new_request.description += additional_info

        db.session.add(new_request)
        db.session.commit()

        # Log request submission
        log_user_action(
            action='create',
            resource_type='project_request',
            resource_id=new_request.id,
            details={
                'project_title': new_request.project_title,
                'priority': new_request.priority.value,
                'form_data': form_data
            }
        )

        # Trigger email notification to admins
        try:
            from backend.services.email_service import EmailService
            email_service = EmailService()
            email_service.send_new_request_notification(new_request)
        except Exception as e:
            logger.error(f"Failed to send new request notification: {str(e)}")
            # Don't fail the request submission if email fails

        logger.info(f"New project request submitted by user {current_user.id}: {new_request.project_title}")

        return jsonify({
            'success': True,
            'message': 'Project request submitted successfully. Admins have been notified.',
            'data': new_request.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting project request: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to submit project request'
        }), 500

@projects_bp.route('/<int:request_id>', methods=['GET'])
@login_required
def get_request(request_id):
    """Get detailed information about a specific request"""
    try:
        request_obj = ProjectRequest.query.filter_by(
            id=request_id, 
            user_id=current_user.id
        ).first()
        
        if not request_obj:
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404

        return jsonify({
            'success': True,
            'data': request_obj.to_dict()
        })

    except Exception as e:
        logger.error(f"Error retrieving request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve request details'
        }), 500

@projects_bp.route('/<int:request_id>/status', methods=['GET'])
@login_required
def request_status(request_id):
    """Get status of a specific request"""
    try:
        request_obj = ProjectRequest.query.filter_by(
            id=request_id, 
            user_id=current_user.id
        ).first()
        
        if not request_obj:
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'id': request_obj.id,
                'project_title': request_obj.project_title,
                'status': request_obj.status.value,
                'submitted_at': request_obj.submitted_at.isoformat(),
                'approved_at': request_obj.approved_at.isoformat() if request_obj.approved_at else None,
                'rejected_at': request_obj.rejected_at.isoformat() if request_obj.rejected_at else None,
                'rejection_reason': request_obj.rejection_reason,
                'hod_approved_at': request_obj.hod_approved_at.isoformat() if request_obj.hod_approved_at else None,
                'faculty_approved_at': request_obj.faculty_approved_at.isoformat() if request_obj.faculty_approved_at else None,
                'lab_incharge_approved_at': request_obj.lab_incharge_approved_at.isoformat() if request_obj.lab_incharge_approved_at else None
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving request status {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve request status'
        }), 500

@projects_bp.route('/<int:request_id>/update', methods=['PUT'])
@login_required
def update_request(request_id):
    """Update a pending project request"""
    try:
        request_obj = ProjectRequest.query.filter_by(
            id=request_id, 
            user_id=current_user.id
        ).first()
        
        if not request_obj:
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404

        # Only allow updates for pending requests
        if request_obj.status != StatusEnum.pending:
            return jsonify({
                'success': False,
                'message': 'Only pending requests can be updated'
            }), 400

        data = request.get_json()
        
        # Update allowed fields
        if 'project_title' in data:
            request_obj.project_title = data['project_title']
        if 'description' in data:
            request_obj.description = data['description']
        if 'purpose' in data:
            request_obj.purpose = data['purpose']
        if 'expected_duration' in data:
            request_obj.expected_duration = data['expected_duration']
        if 'priority' in data:
            if data['priority'] in [p.value for p in PriorityEnum]:
                request_obj.priority = PriorityEnum(data['priority'])

        request_obj.updated_at = datetime.utcnow()
        db.session.commit()

        # Log request update
        log_user_action(
            action='update',
            resource_type='project_request',
            resource_id=request_id,
            details={'updated_fields': list(data.keys())}
        )

        return jsonify({
            'success': True,
            'message': 'Request updated successfully',
            'data': request_obj.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update request'
        }), 500

@projects_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    """Cancel a pending project request"""
    try:
        request_obj = ProjectRequest.query.filter_by(
            id=request_id, 
            user_id=current_user.id
        ).first()
        
        if not request_obj:
            return jsonify({
                'success': False,
                'message': 'Request not found'
            }), 404

        # Only allow cancellation for pending requests
        if request_obj.status != StatusEnum.pending:
            return jsonify({
                'success': False,
                'message': 'Only pending requests can be cancelled'
            }), 400

        # Soft delete by setting status to rejected with cancellation reason
        request_obj.status = StatusEnum.rejected
        request_obj.rejected_at = datetime.utcnow()
        request_obj.rejection_reason = "Cancelled by user"
        request_obj.updated_at = datetime.utcnow()
        
        db.session.commit()

        # Log request cancellation
        log_user_action(
            action='delete',
            resource_type='project_request',
            resource_id=request_id,
            details={'reason': 'user_cancellation'}
        )

        return jsonify({
            'success': True,
            'message': 'Request cancelled successfully'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to cancel request'
        }), 500

@projects_bp.route('/dashboard', methods=['GET'])
@login_required
def user_dashboard():
    """Get dashboard data for the current user"""
    try:
        # Get user's request statistics
        total_requests = ProjectRequest.query.filter_by(user_id=current_user.id).count()
        pending_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id, 
            status=StatusEnum.pending
        ).count()
        approved_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id, 
            status=StatusEnum.approved
        ).count()
        rejected_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id, 
            status=StatusEnum.rejected
        ).count()

        # Get recent requests
        recent_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(ProjectRequest.submitted_at)).limit(5).all()

        # Check NDA status
        nda = NDA.query.filter_by(user_id=current_user.id).first()
        nda_status = {
            'has_nda': nda is not None,
            'is_approved': nda.is_approved if nda else False,
            'upload_date': nda.upload_date.isoformat() if nda else None
        }

        dashboard_data = {
            'user': current_user.to_dict(),
            'statistics': {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'approved_requests': approved_requests,
                'rejected_requests': rejected_requests
            },
            'recent_requests': [req.to_dict() for req in recent_requests],
            'nda_status': nda_status
        }

        return jsonify({
            'success': True,
            'data': dashboard_data
        })

    except Exception as e:
        logger.error(f"Error retrieving user dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve dashboard data'
        }), 500

@projects_bp.route('/analytics', methods=['GET'])
@login_required
def user_analytics():
    """Get analytics data for the current user"""
    try:
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow().replace(day=1)  # First day of current month
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()

        # Get requests in date range
        requests_in_period = ProjectRequest.query.filter(
            and_(
                ProjectRequest.user_id == current_user.id,
                ProjectRequest.submitted_at >= start_date,
                ProjectRequest.submitted_at <= end_date
            )
        ).all()

        # Calculate analytics
        analytics = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'request_statistics': {
                'total_in_period': len(requests_in_period),
                'by_status': {},
                'by_priority': {},
                'by_month': {}
            }
        }

        # Count by status
        for request_obj in requests_in_period:
            status = request_obj.status.value
            analytics['request_statistics']['by_status'][status] = \
                analytics['request_statistics']['by_status'].get(status, 0) + 1

        # Count by priority
        for request_obj in requests_in_period:
            priority = request_obj.priority.value
            analytics['request_statistics']['by_priority'][priority] = \
                analytics['request_statistics']['by_priority'].get(priority, 0) + 1

        return jsonify({
            'success': True,
            'data': analytics
        })

    except Exception as e:
        logger.error(f"Error retrieving user analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve analytics data'
        }), 500