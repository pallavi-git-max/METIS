import os
import logging
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from datetime import datetime
from models.user import User, RoleEnum, DepartmentEnum
from models.nda import NDA
from app import db
from forms.login_form import LoginForm
from utils.validation import validate_user_data, validate_email, validate_password_strength
from utils.error_handlers import ValidationError, BusinessLogicError
from middleware.audit_middleware import log_user_action

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

# Configure logging
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login route supporting all user types"""
    form = LoginForm()
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            user_type = data.get('user_type', 'student')  # student, faculty, admin, external

            if not email or not password:
                return jsonify({
                    'success': False, 
                    'message': 'Email and password are required'
                }), 400

            # Validate email format
            validate_email(email)

            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return jsonify({
                    'success': False, 
                    'message': 'Invalid email or password'
                }), 401

            # Check password
            if not user.check_password(password):
                logger.warning(f"Failed login attempt for user: {email}")
                return jsonify({
                    'success': False, 
                    'message': 'Invalid email or password'
                }), 401

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt by inactive user: {email}")
                return jsonify({
                    'success': False, 
                    'message': 'Account is deactivated. Please contact administrator.'
                }), 401

            # Check user type compatibility
            if user_type == 'admin' and not user.is_admin:
                return jsonify({
                    'success': False, 
                    'message': 'Admin access required'
                }), 403

            # Update last login
            user.update_last_login()
            
            # Login user
            login_user(user, remember=True)
            
            # Log successful login
            log_user_action(
                action='login',
                resource_type='user',
                resource_id=user.id,
                details={'user_type': user_type, 'login_method': 'email'}
            )
            
            logger.info(f"Successful login for user: {email} (ID: {user.id})")
            
            return jsonify({
                'success': True, 
                'message': 'Logged in successfully',
                'data': {
                    'user': user.to_dict(),
                    'redirect_url': get_redirect_url(user.role.value)
                }
            })

        except ValidationError as e:
            return jsonify({
                'success': False, 
                'message': e.message,
                'field': e.field
            }), 400
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': 'An error occurred during login'
            }), 500

    # GET method - serve login page
    return render_template('college-login-system.html', form=form)

def get_redirect_url(role):
    """Get appropriate redirect URL based on user role"""
    redirect_urls = {
        'student': '/dashboard',
        'faculty': '/dashboard',
        'lab_incharge': '/dashboard',
        'hod': '/dashboard',
        'admin': '/admin/dashboard',
        'external': '/dashboard'
    }
    return redirect_urls.get(role, '/dashboard')

@auth_bp.route('/logout')
@login_required
def logout():
    """Enhanced logout with audit logging"""
    user_id = current_user.id
    user_email = current_user.email
    
    # Log logout action
    log_user_action(
        action='logout',
        resource_type='user',
        resource_id=user_id,
        details={'logout_method': 'manual'}
    )
    
    logout_user()
    logger.info(f"User logged out: {user_email} (ID: {user_id})")
    
    return jsonify({
        'success': True, 
        'message': 'Logged out successfully',
        'redirect_url': '/auth/login'
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """Enhanced registration supporting all user types"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Validate user data
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
                'message': 'Email already registered'
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
        new_user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=RoleEnum(data['role']),
            department=DepartmentEnum(data['department']) if data.get('department') else None,
            designation=data.get('designation'),
            student_id=data.get('student_id'),
            phone=data.get('phone'),
            is_active=True
        )
        
        # Set password
        new_user.set_password(data['password'])
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log registration
        log_user_action(
            action='create',
            resource_type='user',
            resource_id=new_user.id,
            details={'registration_method': 'self_registration', 'role': data['role']}
        )
        
        logger.info(f"New user registered: {data['email']} (ID: {new_user.id})")
        
        return jsonify({
            'success': True, 
            'message': 'User registered successfully',
            'data': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Registration failed. Please try again.'
        }), 500

@auth_bp.route('/upload-nda', methods=['POST'])
@login_required
def upload_nda():
    """Enhanced NDA upload with validation and audit logging"""
    try:
        if 'nda_file' not in request.files:
            return jsonify({
                'success': False, 
                'message': 'No file part in the request'
            }), 400

        file = request.files['nda_file']
        if file.filename == '':
            return jsonify({
                'success': False, 
                'message': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'message': 'Invalid file type. Only PDF, DOC, and DOCX files are allowed'
            }), 400

        # Generate secure filename
        filename = secure_filename(file.filename)
        timestamp = int(datetime.utcnow().timestamp())
        name, ext = os.path.splitext(filename)
        filename = f"nda_{current_user.id}_{timestamp}{ext}"
        
        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        save_path = os.path.join(upload_dir, filename)
        file.save(save_path)

        # Check if user already has an NDA
        existing_nda = NDA.query.filter_by(user_id=current_user.id).first()
        if existing_nda:
            # Update existing NDA
            existing_nda.filename = filename
            existing_nda.file_path = save_path
            existing_nda.upload_date = datetime.utcnow()
            existing_nda.is_approved = False  # Reset approval status
            nda = existing_nda
        else:
            # Create new NDA record
            nda = NDA(
                user_id=current_user.id,
                filename=filename,
                file_path=save_path,
                upload_date=datetime.utcnow(),
                is_approved=False
            )
            db.session.add(nda)

        db.session.commit()

        # Log NDA upload
        log_user_action(
            action='create',
            resource_type='nda',
            resource_id=nda.id,
            details={'filename': filename, 'file_size': os.path.getsize(save_path)}
        )

        logger.info(f"NDA uploaded by user {current_user.id}: {filename}")

        return jsonify({
            'success': True, 
            'message': 'NDA uploaded successfully',
            'data': {
                'nda_id': nda.id,
                'filename': filename,
                'upload_date': nda.upload_date.isoformat(),
                'is_approved': nda.is_approved
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"NDA upload error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Failed to upload NDA. Please try again.'
        }), 500

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """Get or update user profile"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Update allowed fields
            if 'first_name' in data:
                current_user.first_name = data['first_name']
            if 'last_name' in data:
                current_user.last_name = data['last_name']
            if 'phone' in data:
                current_user.phone = data['phone']
            if 'designation' in data:
                current_user.designation = data['designation']
            
            current_user.updated_at = datetime.utcnow()
            db.session.commit()

            # Log profile update
            log_user_action(
                action='update',
                resource_type='user',
                resource_id=current_user.id,
                details={'updated_fields': list(data.keys())}
            )

            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'data': current_user.to_dict()
            })

        except Exception as e:
            db.session.rollback()
            logger.error(f"Profile update error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to update profile'
            }), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current password and new password are required'
            }), 400

        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400

        # Validate new password
        validate_password_strength(new_password)

        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        # Log password change
        log_user_action(
            action='update',
            resource_type='user',
            resource_id=current_user.id,
            details={'action': 'password_change'}
        )

        logger.info(f"Password changed for user: {current_user.email}")

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })

    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': e.message,
            'field': e.field
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password change error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to change password'
        }), 500

@auth_bp.route('/check-nda-status', methods=['GET'])
@login_required
def check_nda_status():
    """Check NDA status for current user"""
    try:
        nda = NDA.query.filter_by(user_id=current_user.id).first()
        
        if not nda:
            return jsonify({
                'success': True,
                'data': {
                    'has_nda': False,
                    'is_approved': False,
                    'message': 'No NDA uploaded'
                }
            })

        return jsonify({
            'success': True,
            'data': {
                'has_nda': True,
                'is_approved': nda.is_approved,
                'filename': nda.filename,
                'upload_date': nda.upload_date.isoformat(),
                'approved_date': nda.approved_date.isoformat() if nda.approved_date else None
            }
        })

    except Exception as e:
        logger.error(f"NDA status check error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check NDA status'
        }), 500
