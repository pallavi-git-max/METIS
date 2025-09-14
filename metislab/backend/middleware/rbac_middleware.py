from functools import wraps
from flask import jsonify, request
from flask_login import current_user
from backend.models.user import RoleEnum
import logging

logger = logging.getLogger(__name__)

def require_role(required_roles):
    """
    Decorator to require specific roles for access
    
    Args:
        required_roles: List of roles or single role that can access the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required'
                }), 401

            # Convert single role to list
            if isinstance(required_roles, str):
                allowed_roles = [required_roles]
            else:
                allowed_roles = required_roles

            # Check if user has required role
            if current_user.role.value not in allowed_roles:
                logger.warning(f"Access denied for user {current_user.id} with role {current_user.role.value} to endpoint {request.endpoint}")
                return jsonify({
                    'success': False,
                    'message': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator to require admin role"""
    return require_role('admin')(f)

def require_faculty(f):
    """Decorator to require faculty role (faculty, lab_incharge, hod, admin)"""
    return require_role(['faculty', 'lab_incharge', 'hod', 'admin'])(f)

def require_lab_incharge(f):
    """Decorator to require lab incharge role (lab_incharge, admin)"""
    return require_role(['lab_incharge', 'admin'])(f)

def require_hod(f):
    """Decorator to require HOD role (hod, admin)"""
    return require_role(['hod', 'admin'])(f)

def can_view_request(request_obj):
    """
    Check if current user can view a specific request
    
    Args:
        request_obj: ProjectRequest object
        
    Returns:
        bool: True if user can view the request
    """
    if not current_user.is_authenticated:
        return False

    # Users can always view their own requests
    if request_obj.user_id == current_user.id:
        return True

    # Faculty and admin can view all requests
    if current_user.is_faculty or current_user.is_admin:
        return True

    return False

def can_approve_request(request_obj):
    """
    Check if current user can approve a specific request
    
    Args:
        request_obj: ProjectRequest object
        
    Returns:
        tuple: (can_approve: bool, message: str)
    """
    if not current_user.is_authenticated:
        return False, "Authentication required"

    # Admin can approve any request
    if current_user.is_admin:
        return True, "Admin can approve any request"

    # Check workflow permissions: Lab In-charge → Faculty → HOD → Admin
    from backend.models.project_request import StatusEnum
    
    if current_user.role == RoleEnum.lab_incharge and request_obj.status == StatusEnum.pending:
        return True, "Lab In-charge can approve pending requests"
    
    if current_user.role == RoleEnum.faculty and request_obj.status == StatusEnum.lab_incharge_approved:
        return True, "Faculty can approve lab in-charge approved requests"
    
    if current_user.role == RoleEnum.hod and request_obj.status == StatusEnum.faculty_approved:
        return True, "HoD can approve faculty approved requests"

    return False, "Insufficient permissions to approve this request at current stage"

def can_reject_request(request_obj):
    """
    Check if current user can reject a specific request
    
    Args:
        request_obj: ProjectRequest object
        
    Returns:
        tuple: (can_reject: bool, message: str)
    """
    if not current_user.is_authenticated:
        return False, "Authentication required"

    # Faculty and admin can reject requests
    if current_user.is_faculty or current_user.is_admin:
        return True, "Faculty/Admin can reject requests"

    return False, "Insufficient permissions to reject requests"

def can_manage_user(target_user):
    """
    Check if current user can manage a specific user
    
    Args:
        target_user: User object to be managed
        
    Returns:
        bool: True if user can manage the target user
    """
    if not current_user.is_authenticated:
        return False

    # Users can manage their own profile (limited fields)
    if target_user.id == current_user.id:
        return True

    # Admin can manage all users
    if current_user.is_admin:
        return True

    # Faculty can manage students in their department
    if current_user.is_faculty and target_user.role == RoleEnum.student:
        if current_user.department == target_user.department:
            return True

    return False

def get_user_accessible_requests():
    """
    Get query filter for requests accessible by current user
    
    Returns:
        SQLAlchemy query filter
    """
    from backend.models.project_request import ProjectRequest
    from sqlalchemy import or_

    if not current_user.is_authenticated:
        return ProjectRequest.query.filter(False)  # No access

    # Admin can see all requests
    if current_user.is_admin:
        return ProjectRequest.query

    # Faculty can see all requests
    if current_user.is_faculty:
        return ProjectRequest.query

    # Regular users can only see their own requests
    return ProjectRequest.query.filter_by(user_id=current_user.id)

def get_user_approval_queue():
    """
    Get requests that need approval from current user based on workflow
    
    Returns:
        SQLAlchemy query filter
    """
    from backend.models.project_request import ProjectRequest, StatusEnum

    if not current_user.is_authenticated:
        return ProjectRequest.query.filter(False)  # No access

    # Admin can see requests ready for final approval
    if current_user.is_admin:
        return ProjectRequest.query.filter_by(status=StatusEnum.hod_approved)

    # HoD can see faculty approved requests
    if current_user.role == RoleEnum.hod:
        return ProjectRequest.query.filter_by(status=StatusEnum.faculty_approved)

    # Faculty can see lab in-charge approved requests
    if current_user.role == RoleEnum.faculty:
        return ProjectRequest.query.filter_by(status=StatusEnum.lab_incharge_approved)

    # Lab In-charge can see pending requests
    if current_user.role == RoleEnum.lab_incharge:
        return ProjectRequest.query.filter_by(status=StatusEnum.pending)

    return ProjectRequest.query.filter(False)  # No access

def log_access_attempt(endpoint, success, details=None):
    """
    Log access attempt for audit purposes
    
    Args:
        endpoint: The endpoint being accessed
        success: Whether access was granted
        details: Additional details about the access attempt
    """
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    user_role = current_user.role.value if current_user.is_authenticated else 'none'
    
    log_message = f"Access attempt: {endpoint} by user {user_id} (role: {user_role}) - {'SUCCESS' if success else 'DENIED'}"
    
    if details:
        log_message += f" - {details}"
    
    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)
