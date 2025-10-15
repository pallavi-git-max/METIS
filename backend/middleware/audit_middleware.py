from flask import request, g
from functools import wraps
import json
import logging
from backend.models.audit_log import AuditLog, ActionEnum

logger = logging.getLogger(__name__)

def audit_action(action, resource_type, get_resource_id=None):
    """
    Decorator to automatically log admin actions
    
    Args:
        action: The action being performed (from ActionEnum)
        resource_type: Type of resource being affected ('user', 'project_request', etc.)
        get_resource_id: Function to extract resource ID from response (optional)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user info
            from flask_login import current_user
            user_id = current_user.id if current_user.is_authenticated else None
            
            # Get request info
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent')
            
            # Prepare details
            details = {
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url,
                'args': dict(request.args),
                'data': request.get_json() if request.is_json else None
            }
            
            # Execute the original function
            response = f(*args, **kwargs)
            
            # Log the action
            if user_id:
                try:
                    resource_id = None
                    if get_resource_id and hasattr(response, 'get_json'):
                        response_data = response.get_json()
                        if response_data and response_data.get('success'):
                            resource_id = get_resource_id(response_data)
                    
                    AuditLog.log_action(
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        details=json.dumps(details),
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                except Exception as e:
                    logger.error(f"Failed to log audit action: {str(e)}")
            
            return response
        return decorated_function
    return decorator

def log_user_action(action, resource_type, resource_id=None, details=None):
    """Manually log a user action"""
    from flask_login import current_user
    
    if not current_user.is_authenticated:
        return None
    
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent')
    
    return AuditLog.log_action(
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent
    )
