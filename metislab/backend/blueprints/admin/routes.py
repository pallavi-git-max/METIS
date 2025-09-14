from flask import Blueprint, jsonify, render_template, request, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import logging
from backend.models.user import User, RoleEnum, DepartmentEnum
from backend.models.project_request import ProjectRequest, StatusEnum, PriorityEnum
from backend.models.approval import Approval
from backend.models.nda import NDA
from backend.app import db
from backend.utils.validation import validate_user_data, validate_approval_data

admin_bp = Blueprint('admin', __name__, template_folder='../../templates')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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
        hod_submitted = ProjectRequest.query.filter_by(status=StatusEnum.hod_submitted).count()
        approved_requests = ProjectRequest.query.filter_by(status=StatusEnum.approved).count()
        
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
                ProjectRequest.status == StatusEnum.lab_incharge_approved,
                ProjectRequest.status == StatusEnum.faculty_approved,
                ProjectRequest.status == StatusEnum.hod_approved
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
                'recent_requests': recent_requests_count
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
        search = request.args.get('search')
        
        # Build query
        query = User.query
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if department_filter:
            query = query.filter(User.department == department_filter)
        
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
