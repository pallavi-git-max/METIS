import re
from datetime import datetime
from backend.models.user import RoleEnum, DepartmentEnum

def validate_json_data(data, required_fields):
    """Validate JSON data for required fields"""
    if not data:
        return False, "No data provided"
    
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "Valid"

def validate_user_data(data):
    """Validate user data"""
    required_fields = ['email', 'first_name', 'last_name', 'role']
    is_valid, message = validate_json_data(data, required_fields)
    if not is_valid:
        return False, message
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        return False, "Invalid email format"
    
    # Validate role
    valid_roles = [role.value for role in RoleEnum]
    if data['role'] not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    # Validate department if provided
    if 'department' in data and data['department']:
        valid_departments = [dept.value for dept in DepartmentEnum]
        if data['department'] not in valid_departments:
            return False, f"Invalid department. Must be one of: {', '.join(valid_departments)}"
    
    return True, "Valid"

def validate_request_data(data):
    """Validate project request data"""
    required_fields = ['project_title', 'description', 'purpose']
    is_valid, message = validate_json_data(data, required_fields)
    if not is_valid:
        return False, message
    
    # Validate priority if provided
    if 'priority' in data and data['priority']:
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if data['priority'] not in valid_priorities:
            return False, f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
    
    return True, "Valid"

def validate_approval_data(data):
    """Validate approval data"""
    if not data:
        return False, "No data provided"
    
    if 'approved' not in data:
        return False, "Approval status is required"
    
    if not isinstance(data['approved'], bool):
        return False, "Approval status must be boolean"
    
    if not data['approved'] and 'reason' not in data:
        return False, "Rejection reason is required for rejected requests"
    
    return True, "Valid"
