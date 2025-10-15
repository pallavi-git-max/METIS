import logging
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from backend.models.user import User
from backend.models.project_request import ProjectRequest, StatusEnum
from backend.models.nda import NDA
from backend.models.approval import Approval
from backend.models import db
from backend.middleware.audit_middleware import log_user_action

user_dashboard_bp = Blueprint('user_dashboard', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@user_dashboard_bp.route('/first-name', methods=['GET'])
@login_required
def first_name():
    """Return the current user's first name (for lightweight UI bindings)."""
    try:
        return jsonify({
            'success': True,
            'first_name': (current_user.first_name or '').strip()
        })
    except Exception as e:
        logger.error(f"Error retrieving first name: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to retrieve first name'}), 500

@user_dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Get comprehensive dashboard data for the current user"""
    try:
        # For external users, they might not have project requests
        # So we'll handle this gracefully
        if current_user.role.value == 'external':
            # External users have limited access - no project requests
            total_requests = 0
            pending_requests = 0
            hod_submitted = 0
            approved_requests = 0
            rejected_requests = 0
        else:
            # Get user's request statistics for students/faculty
            total_requests = ProjectRequest.query.filter_by(user_id=current_user.id).count()
            pending_requests = ProjectRequest.query.filter_by(
                user_id=current_user.id, 
                status=StatusEnum.pending
            ).count()
            hod_submitted = ProjectRequest.query.filter_by(
                user_id=current_user.id, 
                status=StatusEnum.hod_approved
            ).count()
            approved_requests = ProjectRequest.query.filter_by(
                user_id=current_user.id, 
                status=StatusEnum.approved
            ).count()
            rejected_requests = ProjectRequest.query.filter_by(
                user_id=current_user.id, 
                status=StatusEnum.rejected
            ).count()

        # Get recent requests (last 5) - only for non-external users
        if current_user.role.value == 'external':
            recent_requests = []
            requests_by_status = {}
            nda_status = {
                'has_nda': False,
                'is_approved': False,
                'upload_date': None,
                'approved_date': None
            }
            recent_activity = []
        else:
            recent_requests = ProjectRequest.query.filter_by(
                user_id=current_user.id
            ).order_by(desc(ProjectRequest.submitted_at)).limit(5).all()

            # Get requests by status for progress tracking
            requests_by_status = {}
            for status in StatusEnum:
                count = ProjectRequest.query.filter_by(
                    user_id=current_user.id, 
                    status=status
                ).count()
                requests_by_status[status.value] = count

            # Check NDA status
            nda = NDA.query.filter_by(user_id=current_user.id).first()
            nda_status = {
                'has_nda': nda is not None,
                'is_approved': nda.is_approved if nda else False,
                'upload_date': nda.upload_date.isoformat() if nda else None,
                'approved_date': nda.approved_date.isoformat() if nda and nda.approved_date else None
            }

            # Get recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_activity = ProjectRequest.query.filter(
                ProjectRequest.user_id == current_user.id,
                ProjectRequest.submitted_at >= thirty_days_ago
            ).order_by(desc(ProjectRequest.submitted_at)).all()

        # Calculate completion rate
        total_submitted = total_requests
        completion_rate = (approved_requests / total_submitted * 100) if total_submitted > 0 else 0

        # Prepare dashboard data
        dashboard_data = {
            'user': current_user.to_dict(),
            'statistics': {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'hod_submitted': hod_submitted,
                'approved_requests': approved_requests,
                'rejected_requests': rejected_requests,
                'completion_rate': round(completion_rate, 2)
            },
            'requests_by_status': requests_by_status,
            'recent_requests': [req.to_dict() for req in recent_requests],
            'recent_activity': [req.to_dict() for req in recent_activity],
            'nda_status': nda_status,
            'last_updated': datetime.utcnow().isoformat()
        }

        # Add external user specific information
        if current_user.role.value == 'external':
            dashboard_data['external_info'] = {
                'aadhar_card': current_user.aadhar_card,
                'profession': current_user.profession,
                'institution': current_user.institution,
                'address': current_user.address,
                'pincode': current_user.pincode,
                'city': current_user.city,
                'state': current_user.state,
                'campus': current_user.campus.value if current_user.campus else None
            }
            # Override statistics for external users
            dashboard_data['statistics'] = {
                'total_requests': 0,
                'pending_requests': 0,
                'hod_submitted': 0,
                'approved_requests': 0,
                'rejected_requests': 0,
                'completion_rate': 0
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

@user_dashboard_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """Get or update user profile"""
    if request.method == 'GET':
        try:
            # Get user profile with additional computed fields
            profile_data = current_user.to_dict()
            
            # Add additional profile information
            profile_data['request_count'] = ProjectRequest.query.filter_by(user_id=current_user.id).count()
            profile_data['nda_uploaded'] = NDA.query.filter_by(user_id=current_user.id).first() is not None
            
            return jsonify({
                'success': True,
                'data': profile_data
            })

        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve profile data'
            }), 500

    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update allowed fields
            updated_fields = []
            if 'first_name' in data and data['first_name']:
                current_user.first_name = data['first_name']
                updated_fields.append('first_name')
            
            if 'last_name' in data and data['last_name']:
                current_user.last_name = data['last_name']
                updated_fields.append('last_name')
            
            if 'phone' in data:
                current_user.phone = data['phone']
                updated_fields.append('phone')
            
            if 'designation' in data:
                current_user.designation = data['designation']
                updated_fields.append('designation')
            
            if updated_fields:
                current_user.updated_at = datetime.utcnow()
                db.session.commit()

                # Log profile update
                log_user_action(
                    action='update',
                    resource_type='user',
                    resource_id=current_user.id,
                    details={'updated_fields': updated_fields}
                )

            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'data': current_user.to_dict()
            })

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user profile: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update profile'
            }), 500

@user_dashboard_bp.route('/requests', methods=['GET'])
@login_required
def my_requests():
    """Get all requests for the current user with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        search = request.args.get('search')
        
        # Build query
        query = ProjectRequest.query.filter_by(user_id=current_user.id)
        
        if status_filter:
            query = query.filter(ProjectRequest.status == status_filter)
        
        if priority_filter:
            query = query.filter(ProjectRequest.priority == priority_filter)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                ProjectRequest.project_title.ilike(search_term)
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
        logger.error(f"Error retrieving user requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve requests'
        }), 500

@user_dashboard_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_request():
    """Get submission form or submit a new request"""
    if request.method == 'GET':
        # Return form configuration or template
        return jsonify({
            'success': True,
            'data': {
                'form_fields': {
                    'fields_of_interest': [
                        'machine-learning', 'deep-learning', 'nlp', 
                        'generative-ai', 'computer-vision', 'vision-language',
                        'cyber-security', 'quantum-ml'
                    ],
                    'package_options': [
                        'basic', 'moderate', 'advance'
                    ],
                    'dataset_status': [
                        'have', 'download', 'create'
                    ],
                    'dataset_sizes': [
                        '<200mb', '200-500mb', '500mb-1gb', '1-5gb', '>5gb'
                    ],
                    'data_types': [
                        'text', 'image', 'speech', 'video', 'sensor', 'geospatial'
                    ],
                    'computational_requirements': [
                        '<5', '5-10', '10-15'
                    ],
                    'priorities': [
                        'low', 'medium', 'high', 'urgent'
                    ]
                },
                'nda_required': True,
                'nda_status': check_nda_status()
            }
        })
    
    elif request.method == 'POST':
        # This would be handled by the projects blueprint
        return jsonify({
            'success': False,
            'message': 'Use /projects/submit endpoint for request submission'
        }), 400

def check_nda_status():
    """Check NDA status for current user"""
    nda = NDA.query.filter_by(user_id=current_user.id).first()
    return {
        'has_nda': nda is not None,
        'is_approved': nda.is_approved if nda else False,
        'upload_date': nda.upload_date.isoformat() if nda else None
    }

@user_dashboard_bp.route('/analytics', methods=['GET'])
@login_required
def analytics():
    """Get detailed analytics for the current user"""
    try:
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days
        
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()

        # Get all user requests
        all_requests = ProjectRequest.query.filter_by(user_id=current_user.id).all()
        
        # Get requests in date range
        requests_in_period = ProjectRequest.query.filter(
            ProjectRequest.user_id == current_user.id,
            ProjectRequest.submitted_at >= start_date,
            ProjectRequest.submitted_at <= end_date
        ).all()

        # Calculate comprehensive analytics
        analytics_data = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'overall_statistics': {
                'total_requests': len(all_requests),
                'requests_in_period': len(requests_in_period),
                'approval_rate': 0,
                'average_processing_time': 0
            },
            'status_breakdown': {},
            'priority_breakdown': {},
            'monthly_trends': {},
            'processing_times': []
        }

        # Calculate approval rate
        approved_count = len([r for r in all_requests if r.status == StatusEnum.approved])
        if all_requests:
            analytics_data['overall_statistics']['approval_rate'] = round(
                (approved_count / len(all_requests)) * 100, 2
            )

        # Status breakdown
        for status in StatusEnum:
            count = len([r for r in all_requests if r.status == status])
            analytics_data['status_breakdown'][status.value] = count

        # Priority breakdown
        from backend.models.project_request import PriorityEnum
        for priority in PriorityEnum:
            count = len([r for r in all_requests if r.priority == priority])
            analytics_data['priority_breakdown'][priority.value] = count

        # Monthly trends
        monthly_data = {}
        for request_obj in requests_in_period:
            month_key = request_obj.submitted_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'submitted': 0, 'approved': 0, 'rejected': 0}
            monthly_data[month_key]['submitted'] += 1
            if request_obj.status == StatusEnum.approved:
                monthly_data[month_key]['approved'] += 1
            elif request_obj.status == StatusEnum.rejected:
                monthly_data[month_key]['rejected'] += 1

        analytics_data['monthly_trends'] = monthly_data

        # Calculate processing times for approved requests
        processing_times = []
        for request_obj in all_requests:
            if request_obj.status == StatusEnum.approved and request_obj.approved_at:
                processing_time = (request_obj.approved_at - request_obj.submitted_at).days
                processing_times.append(processing_time)

        if processing_times:
            analytics_data['overall_statistics']['average_processing_time'] = round(
                sum(processing_times) / len(processing_times), 1
            )

        analytics_data['processing_times'] = processing_times

        return jsonify({
            'success': True,
            'data': analytics_data
        })

    except Exception as e:
        logger.error(f"Error retrieving user analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve analytics data'
        }), 500

@user_dashboard_bp.route('/requests/<int:request_id>', methods=['GET'])
@login_required
def get_request_details(request_id):
    """Get detailed information about a specific request for the current user"""
    try:
        logger.info(f"Fetching request details for request_id={request_id}, user_id={current_user.id}")
        
        # Get the request and ensure it belongs to the current user
        request_obj = ProjectRequest.query.filter_by(
            id=request_id, 
            user_id=current_user.id
        ).first()
        
        if not request_obj:
            logger.warning(f"Request {request_id} not found or does not belong to user {current_user.id}")
            return jsonify({
                'success': False,
                'message': 'Request not found or access denied'
            }), 404
        
        # Get approval history if any
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

@user_dashboard_bp.route('/activities', methods=['GET'])
@login_required
def get_activities():
    """Get all recent activities for the current user"""
    try:
        # Get all project requests for the user
        all_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(ProjectRequest.submitted_at)).all()
        
        # Format activities
        activities = []
        for request in all_requests:
            # Create activity for request submission
            activities.append({
                'id': f"req_{request.id}",
                'type': 'request_submitted',
                'title': 'Request Submitted',
                'description': f'Project request "{request.project_title}" was submitted',
                'timestamp': request.submitted_at.isoformat(),
                'status': request.status.value,
                'request_id': request.id,
                'icon': '📝',
                'color': 'blue'
            })
            
            # Add approval activities if applicable
            if request.guide_approved_at:
                activities.append({
                    'id': f"guide_approval_{request.id}",
                    'type': 'guide_approved',
                    'title': 'Guide Approved',
                    'description': f'Request "{request.project_title}" was approved by guide',
                    'timestamp': request.guide_approved_at.isoformat(),
                    'status': 'guide_approved',
                    'request_id': request.id,
                    'icon': '✅',
                    'color': 'green'
                })
            
            if request.hod_approved_at:
                activities.append({
                    'id': f"hod_approval_{request.id}",
                    'type': 'hod_approved',
                    'title': 'HOD Approved',
                    'description': f'Request "{request.project_title}" was approved by HOD',
                    'timestamp': request.hod_approved_at.isoformat(),
                    'status': 'hod_approved',
                    'request_id': request.id,
                    'icon': '👨‍💼',
                    'color': 'blue'
                })
            
            if request.approved_at:
                activities.append({
                    'id': f"final_approval_{request.id}",
                    'type': 'final_approved',
                    'title': 'Request Approved',
                    'description': f'Request "{request.project_title}" was finally approved',
                    'timestamp': request.approved_at.isoformat(),
                    'status': 'approved',
                    'request_id': request.id,
                    'icon': '🎉',
                    'color': 'green'
                })
            
            if request.rejected_at:
                activities.append({
                    'id': f"rejection_{request.id}",
                    'type': 'request_rejected',
                    'title': 'Request Rejected',
                    'description': f'Request "{request.project_title}" was rejected',
                    'timestamp': request.rejected_at.isoformat(),
                    'status': 'rejected',
                    'request_id': request.id,
                    'icon': '❌',
                    'color': 'red'
                })
        
        # Sort activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'activities': activities,
                'total_count': len(activities)
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving activities: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve activities'
        }), 500

@user_dashboard_bp.route('/notifications', methods=['GET'])
@login_required
def notifications():
    """Get notifications for the current user"""
    try:
        # Get recent requests with status changes
        recent_requests = ProjectRequest.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(ProjectRequest.updated_at)).limit(10).all()

        notifications = []
        for request_obj in recent_requests:
            # Create notification based on status
            if request_obj.status == StatusEnum.approved:
                notifications.append({
                    'id': f"req_{request_obj.id}_approved",
                    'type': 'success',
                    'title': 'Request Approved',
                    'message': f'Your request "{request_obj.project_title}" has been approved.',
                    'timestamp': request_obj.approved_at.isoformat() if request_obj.approved_at else request_obj.updated_at.isoformat(),
                    'request_id': request_obj.id
                })
            elif request_obj.status == StatusEnum.rejected:
                notifications.append({
                    'id': f"req_{request_obj.id}_rejected",
                    'type': 'error',
                    'title': 'Request Rejected',
                    'message': f'Your request "{request_obj.project_title}" has been rejected.',
                    'timestamp': request_obj.rejected_at.isoformat() if request_obj.rejected_at else request_obj.updated_at.isoformat(),
                    'request_id': request_obj.id,
                    'reason': request_obj.rejection_reason
                })
            elif request_obj.status == StatusEnum.hod_approved:
                notifications.append({
                    'id': f"req_{request_obj.id}_hod_approved",
                    'type': 'info',
                    'title': 'Request Forwarded',
                    'message': f'Your request "{request_obj.project_title}" has been forwarded.',
                    'timestamp': request_obj.hod_approved_at.isoformat() if request_obj.hod_approved_at else request_obj.updated_at.isoformat(),
                    'request_id': request_obj.id
                })

        # Sort by timestamp
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'notifications': notifications,
                'unread_count': len(notifications)  # In a real app, you'd track read status
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve notifications'
        }), 500
