from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import logging
from backend.models import db

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class BusinessLogicError(Exception):
    """Custom business logic error"""
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        logger.warning(f"Validation error: {error.message}")
        return jsonify({
            'success': False,
            'message': error.message,
            'field': error.field,
            'error_type': 'validation_error'
        }), 400
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error):
        """Handle business logic errors"""
        logger.warning(f"Business logic error: {error.message}")
        return jsonify({
            'success': False,
            'message': error.message,
            'code': error.code,
            'error_type': 'business_logic_error'
        }), 400
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {error.code}: {error.description}")
        return jsonify({
            'success': False,
            'message': error.description,
            'error_code': error.code,
            'error_type': 'http_error'
        }), error.code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error_type': 'not_found'
        }), 404
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 errors"""
        return jsonify({
            'success': False,
            'message': 'Access forbidden',
            'error_type': 'forbidden'
        }), 403
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 errors"""
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'internal_error'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle generic exceptions"""
        db.session.rollback()
        logger.error(f"Unhandled error: {str(error)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
            'error_type': 'generic_error'
        }), 500

def validate_required_fields(data, required_fields):
    """Validate that required fields are present"""
    if not data:
        raise ValidationError("No data provided")
    
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_email(email):
    """Validate email format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", "email")

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", "password")
    
    if not any(c.isupper() for c in password):
        raise ValidationError("Password must contain at least one uppercase letter", "password")
    
    if not any(c.islower() for c in password):
        raise ValidationError("Password must contain at least one lowercase letter", "password")
    
    if not any(c.isdigit() for c in password):
        raise ValidationError("Password must contain at least one digit", "password")

def validate_phone_number(phone):
    """Validate phone number format"""
    import re
    phone_pattern = r'^\+?1?\d{9,15}$'
    if phone and not re.match(phone_pattern, phone):
        raise ValidationError("Invalid phone number format", "phone")
