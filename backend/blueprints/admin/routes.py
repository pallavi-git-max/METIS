from flask import Blueprint, jsonify, render_template, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import logging
from backend.models.user import User, RoleEnum, DepartmentEnum
from backend.models.project_request import ProjectRequest, StatusEnum, PriorityEnum
from backend.models.approval import Approval
from backend.models.nda import NDA
from backend.models import db
from backend.utils.validation import validate_user_data, validate_approval_data

admin_bp = Blueprint('admin', __name__, template_folder='../../templates')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require elevated roles for admin shell (admin + approver roles)"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        allowed_roles = {RoleEnum.admin, RoleEnum.project_guide, RoleEnum.hod, RoleEnum.it_services}
        if current_user.role not in allowed_roles:
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'} with role {current_user.role}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/profile', methods=['GET'])
@login_required
@admin_required
def admin_profile():
    """Get current admin user profile data"""
    try:
        # Handle department - can be either Enum or string
        department_value = None
        if current_user.department:
            try:
                # Try to get .value (for Enum)
                department_value = current_user.department.value
            except AttributeError:
                # It's already a string
                department_value = current_user.department
        
        admin_data = {
            'id': current_user.id,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'full_name': f"{current_user.first_name} {current_user.last_name}".strip(),
            'role': current_user.role.value if current_user.role else 'admin',
            'student_id': current_user.student_id,
            'phone': current_user.phone,
            'designation': current_user.designation,
            'department': department_value,
            'is_active': current_user.is_active,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None
        }
        
        return jsonify({
            'success': True,
            'admin': admin_data
        })
    except Exception as e:
        logger.error(f"Error fetching admin profile: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to fetch admin profile'
        }), 500

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def dashboard():
    """Get dashboard statistics and data"""
    try:
        # Get basic counts
        total_users = User.query.count()
        total_requests = ProjectRequest.query.count()
        pending_requests = ProjectRequest.query.filter_by(status=StatusEnum.pending).count()
        # In the new workflow there is no 'hod_submitted'. Use HOD approved as an intermediate stage metric.
        hod_submitted = ProjectRequest.query.filter_by(status=StatusEnum.hod_approved).count()
        approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()

        # Real user stats
        active_users_count = User.query.filter_by(is_active=True).count()
        students_count = User.query.filter_by(role=RoleEnum.student).count()
        faculty_external_count = User.query.filter(
            User.role.in_(
                [
                    RoleEnum.faculty,
                    RoleEnum.project_guide,
                    RoleEnum.hod,
                    RoleEnum.it_services,
                    RoleEnum.external,
                    RoleEnum.admin,
                ]
            )
        ).count()
        
        # Get recent activity
        recent_requests = ProjectRequest.query.order_by(desc(ProjectRequest.submitted_at)).limit(5).all()
        active_users = User.query.filter_by(is_active=True).order_by(desc(User.last_login)).limit(5).all()
        
        # Get statistics for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        recent_requests_count = ProjectRequest.query.filter(ProjectRequest.submitted_at >= thirty_days_ago).count()
        
        # Get pending approvals for admin dashboard (all stages)
        pending_approvals = ProjectRequest.query.filter(
            or_(
                ProjectRequest.status == StatusEnum.pending,
                ProjectRequest.status == StatusEnum.guide_approved,
                ProjectRequest.status == StatusEnum.hod_approved,
                ProjectRequest.status == StatusEnum.it_services_approved
            )
        ).order_by(desc(ProjectRequest.submitted_at)).limit(10).all()
        
        dashboard_data = {
            'stats': {
                'total_users': total_users,
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'hod_submitted': hod_submitted,
                'approved_requests': approved_requests,
                'recent_users': recent_users,
                'recent_requests': recent_requests_count,
                'active_users': active_users_count,
                'students_count': students_count,
                'faculty_external_count': faculty_external_count
            },
            'recent_requests': [req.to_dict() for req in recent_requests],
            'active_users': [user.to_dict() for user in active_users],
            'pending_approvals': [req.to_dict() for req in pending_approvals]
        }
        
        logger.info(f"Dashboard data retrieved for admin {current_user.id}")
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve dashboard data'
        }), 500

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Get all users with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role_filter = request.args.get('role')
        department_filter = request.args.get('department')
        is_active_filter = request.args.get('is_active')
        search = request.args.get('search')
        
        # Build query
        query = User.query
        
        if role_filter:
            try:
                query = query.filter(User.role == RoleEnum(role_filter))
            except Exception:
                pass
        
        if department_filter:
            try:
                query = query.filter(User.department == DepartmentEnum(department_filter))
            except Exception:
                pass

        if is_active_filter is not None:
            if is_active_filter.lower() in ['true', '1', 'yes']:
                query = query.filter(User.is_active.is_(True))
            elif is_active_filter.lower() in ['false', '0', 'no']:
                query = query.filter(User.is_active.is_(False))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.student_id.ilike(search_term)
                )
            )
        
        # Paginate results
        users = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': users.total,
                    'pages': users.pages,
                    'has_next': users.has_next,
                    'has_prev': users.has_prev
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve users'
        }), 500

@admin_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        is_valid, message = validate_user_data(data)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email already exists'
            }), 400
        
        # Check if student_id already exists (if provided)
        if 'student_id' in data and data['student_id']:
            existing_student = User.query.filter_by(student_id=data['student_id']).first()
            if existing_student:
                return jsonify({
                    'success': False,
                    'message': 'Student ID already exists'
                }), 400
        
        # Create new user
        user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=RoleEnum(data['role']),
            department=DepartmentEnum(data['department']) if data.get('department') else None,
            designation=data.get('designation'),
            student_id=data.get('student_id'),
            phone=data.get('phone'),
            is_active=data.get('is_active', True)
        )
        
        # Set password
        password = data.get('password', 'defaultpassword123')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user created by admin {current_user.id}: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'data': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create user'
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user information"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Update fields if provided
        if 'email' in data:
            # Check if email already exists for another user
            existing_user = User.query.filter(
                and_(User.email == data['email'], User.id != user_id)
            ).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Email already exists'
                }), 400
            user.email = data['email']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        if 'role' in data:
            if data['role'] not in [role.value for role in RoleEnum]:
                return jsonify({
                    'success': False,
                    'message': 'Invalid role'
                }), 400
            user.role = RoleEnum(data['role'])
        
        if 'department' in data:
            if data['department'] and data['department'] not in [dept.value for dept in DepartmentEnum]:
                return jsonify({
                    'success': False,
                    'message': 'Invalid department'
                }), 400
            user.department = DepartmentEnum(data['department']) if data['department'] else None
        
        if 'designation' in data:
            user.designation = data['designation']
        
        if 'student_id' in data:
            if data['student_id']:
                existing_student = User.query.filter(
                    and_(User.student_id == data['student_id'], User.id != user_id)
                ).first()
                if existing_student:
                    return jsonify({
                        'success': False,
                        'message': 'Student ID already exists'
                    }), 400
            user.student_id = data['student_id']
        
        if 'phone' in data:
            user.phone = data['phone']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {user_id} updated by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update user'
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user (soft delete by deactivating)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Cannot delete your own account'
            }), 400
        
        # Soft delete by deactivating
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {user_id} deactivated by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User deactivated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete user'
        }), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Cannot deactivate your own account'
            }), 400
        
        # Toggle status
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        action = "activated" if user.is_active else "deactivated"
        logger.info(f"User {user_id} {action} by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'User {action} successfully',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user {user_id} status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update user status'
        }), 500

@admin_bp.route('/requests/all', methods=['GET'])
@login_required
def get_all_requests():
    """Get all requests with filtering and pagination"""
    try:
        from sqlalchemy.orm import joinedload
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # Build query with eager loading of user relationship
        query = ProjectRequest.query.options(joinedload(ProjectRequest.user))
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = StatusEnum(status_filter)
                query = query.filter_by(status=status_enum)
            except ValueError:
                pass
        
        # Apply search filter - search by request ID
        if search:
            try:
                # Try to convert to integer for ID search
                request_id = int(search)
                query = query.filter(ProjectRequest.id == request_id)
            except ValueError:
                # If not a valid integer, search by title/description/user
                search_term = f'%{search}%'
                query = query.filter(
                    or_(
                        ProjectRequest.project_title.ilike(search_term),
                        ProjectRequest.description.ilike(search_term)
                    )
                )
        
        # Order by most recent first
        query = query.order_by(desc(ProjectRequest.submitted_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'requests': [req.to_dict() for req in pagination.items],
                'pagination': {
                    'current_page': pagination.page,
                    'total_pages': pagination.pages,
                    'total_items': pagination.total,
                    'per_page': per_page,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error fetching all requests: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Failed to fetch requests: {str(e)}'
        }), 500

@admin_bp.route('/requests/<int:request_id>/close', methods=['POST'])
@login_required
@admin_required
def close_request(request_id):
    """Close a request after it has been used (admin only)"""
    try:
        request_obj = ProjectRequest.query.get_or_404(request_id)
        
        # Only approved requests can be closed
        if request_obj.status != StatusEnum.approved:
            return jsonify({
                'success': False,
                'message': 'Only approved requests can be closed'
            }), 400
        
        # Mark as closed
        request_obj.status = StatusEnum.closed
        request_obj.closed_at = datetime.utcnow()
        request_obj.closed_by = current_user.id
        
        db.session.commit()
        
        logger.info(f"Request {request_id} closed by admin {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Request marked as closed successfully',
            'data': request_obj.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error closing request {request_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to close request'
        }), 500
