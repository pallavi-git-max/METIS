import os
import logging
import time
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from datetime import datetime, timedelta
from backend.models.user import User, RoleEnum, CampusEnum
from backend.models.nda import NDA
from backend.models import db
from backend.forms.login_form import LoginForm
from backend.utils import validate_user_data, validate_email, validate_password_strength
from backend.utils.error_handlers import ValidationError, BusinessLogicError
from backend.middleware.audit_middleware import log_user_action
from backend.services.email_service import EmailService
from backend.utils.database_utils import retry_on_locking_error, safe_db_operation

auth_bp = Blueprint('auth', __name__, template_folder='../../templates')

# Configure logging
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced login route supporting all user types"""
    form = LoginForm()
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            identifier = (data.get('email') or '').strip()
            password = (data.get('password') or '').strip()
            user_type = data.get('user_type', 'student')  # student, faculty, admin, external

            if not identifier or not password:
                return jsonify({
                    'success': False, 
                    'message': 'Email and password are required'
                }), 400

            # Determine whether identifier is an email or an ID
            is_email = '@' in identifier
            if is_email:
                # Validate email format only if it's an email
                validate_email(identifier)
                def find_user_by_email():
                    return User.query.filter_by(email=identifier).first()
                user = safe_db_operation(find_user_by_email)
            else:
                # Try student_id/employee id field
                def find_user_by_id():
                    return User.query.filter_by(student_id=identifier).first()
                user = safe_db_operation(find_user_by_id)
            
            if not user:
                logger.warning(f"Login attempt with non-existent identifier: {identifier}")
                return jsonify({
                    'success': False, 
                    'message': 'Invalid email or password'
                }), 401

            # Check password
            if not user.check_password(password):
                logger.warning(f"Failed login attempt for user: {identifier}")
                return jsonify({
                    'success': False, 
                    'message': 'Invalid email or password'
                }), 401

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt by inactive user: {identifier}")
                return jsonify({
                    'success': False, 
                    'message': 'Account is deactivated. Please contact administrator.'
                }), 401

            # Check user type compatibility
            # Allow the admin portal to be used by elevated roles as well
            if user_type == 'admin':
                allowed_roles = {
                    RoleEnum.admin,
                    RoleEnum.project_guide,
                    RoleEnum.hod,
                    RoleEnum.it_services
                }
                if user.role not in allowed_roles:
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
            
            redirect_url = get_redirect_url(user.role.value)
            logger.info(f"Successful login for user: {user.email} (ID: {user.id}, Role: {user.role.value}, Redirect: {redirect_url})")
            
            return jsonify({
                'success': True, 
                'message': 'Logged in successfully',
                'data': {
                    'user': user.to_dict(),
                    'redirect_url': redirect_url
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
        'project_guide': '/admin_dash.html',
        'hod': '/admin_dash.html',
        'it_services': '/admin_dash.html',
        # Admin gets full management dashboard
        'admin': '/admin_dash.html',
        'external': '/dashboard'
    }
    return redirect_urls.get(role, '/dashboard')

@auth_bp.route('/logout', methods=['GET', 'POST'])
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
        'redirect_url': '/college-login-system.html'
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """Enhanced registration supporting all user types"""
    try:
        # Check if request is multipart (with file) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            profile_photo = request.files.get('profile_photo')
        else:
            data = request.get_json()
            profile_photo = None
        
        logger.info(f"Registration attempt - Data received: {list(data.keys())}")
        logger.info(f"Profile photo present: {profile_photo is not None}")
        
        # Validate required fields (password not required; generated server-side)
        required_fields = ['email', 'first_name', 'last_name', 'role', 'department']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.error(f"Missing required field: {field}")
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Validate user data
        is_valid, message = validate_user_data(data)
        if not is_valid:
            logger.error(f"Validation failed: {message}")
            return jsonify({
                'success': False, 
                'message': message
            }), 400

        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            logger.error(f"Email already registered: {data['email']}")
            return jsonify({
                'success': False, 
                'message': 'Email already registered'
            }), 400

        # Check if student_id already exists (if provided)
        if 'student_id' in data and data['student_id']:
            existing_student = User.query.filter_by(student_id=data['student_id']).first()
            if existing_student:
                logger.error(f"Student ID already exists: {data['student_id']}")
                return jsonify({
                    'success': False, 
                    'message': 'Student ID already exists'
                }), 400
        
        # Handle profile photo upload
        photo_filename = None
        if profile_photo and profile_photo.filename:
            if not allowed_image_file(profile_photo.filename):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image file type. Only JPG, JPEG, and PNG are allowed'
                }), 400
            
            # Check file size (2MB limit)
            profile_photo.seek(0, os.SEEK_END)
            file_size = profile_photo.tell()
            profile_photo.seek(0)
            if file_size > 2 * 1024 * 1024:
                return jsonify({
                    'success': False,
                    'message': 'Profile photo must be less than 2MB'
                }), 400
            
            # Generate secure filename
            filename = secure_filename(profile_photo.filename)
            timestamp = int(datetime.utcnow().timestamp())
            name, ext = os.path.splitext(filename)
            photo_filename = f"profile_{timestamp}_{name}{ext}"
            
            # Ensure upload directory exists
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            save_path = os.path.join(upload_dir, photo_filename)
            profile_photo.save(save_path)

        # Create new user (initially without student_id; we'll generate below if missing)
        new_user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=RoleEnum(data['role']),
            department=data.get('department') if data.get('department') else None,
            campus=CampusEnum(data['campus']) if data.get('campus') else None,
            designation=data.get('designation'),
            student_id=data.get('student_id'),
            phone=data.get('phone'),
            profile_photo=photo_filename,
            is_active=True
        )

        # Generate unique user ID (student_id) if not provided: MET<NNNNNN>
        # Example: MET000001, MET000002
        try:
            if not new_user.student_id:
                prefix = "MET"
                last_user = (
                    User.query
                        .filter(User.student_id.like(f"{prefix}%"))
                        .order_by(User.student_id.desc())
                        .first()
                )
                next_seq = 1
                if last_user and last_user.student_id:
                    try:
                        digits = ''.join([c for c in last_user.student_id if c.isdigit()])
                        last_seq = int(digits) if digits else 0
                        next_seq = last_seq + 1
                    except Exception:
                        next_seq = 1
                new_user.student_id = f"{prefix}{next_seq:06d}"
        except Exception:
            # If generation fails, leave as None
            pass
        
        # Generate password per new policy for non-admins:
        # 3 letters from first name, last 3 digits of phone, 3 random chars
        raw_password = data.get('password')
        if new_user.role != RoleEnum.admin:
            try:
                first = (new_user.first_name or '').strip()
                name_part = (first[:3] if len(first) >= 3 else (first + 'xxx')[:3]).lower()
                phone_digits = ''.join([c for c in (new_user.phone or '') if c.isdigit()])
                phone_part = (phone_digits[-3:] if len(phone_digits) >= 3 else (('000' + phone_digits)[-3:]))
                import random, string
                rand_part = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(3))
                raw_password = name_part + phone_part + rand_part
            except Exception:
                raw_password = 'abc123xyz'  # fallback
        else:
            # For admins registering via this endpoint, still allow optional explicit password
            if not raw_password:
                raw_password = 'Admin@123456'  # minimal default for admins if omitted

        # Set password
        new_user.set_password(raw_password)
        
        # Save to database with retry logic
        def save_user():
            db.session.add(new_user)
            db.session.commit()
        
        safe_db_operation(save_user)

        # Send welcome/credentials email (non-admins) or expose temp password in dev when SMTP not set
        try:
            if new_user.role != RoleEnum.admin:
                sent = EmailService().send_welcome_email(new_user, raw_password)
                if not sent:
                    logger.warning("SMTP not configured or send failed; returning temp password in response for development use")
        except Exception as _e:
            logger.warning(f"Credential email send failed for {new_user.email}: {_e}")
        
        # Log registration
        log_user_action(
            action='create',
            resource_type='user',
            resource_id=new_user.id,
            details={'registration_method': 'self_registration', 'role': data['role']}
        )
        
        logger.info(f"New user registered: {data['email']} (ID: {new_user.id})")
        
        response_data = {
            'success': True,
            'message': 'User registered successfully',
            'data': new_user.to_dict()
        }
        # In development, if SMTP creds are missing, include temp password so user can log in
        try:
            smtp_user = current_app.config.get('SMTP_USERNAME')
            smtp_pass = current_app.config.get('SMTP_PASSWORD')
            if not smtp_user or not smtp_pass or current_app.debug:
                response_data['data']['temporary_password'] = raw_password
        except Exception:
            pass

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Registration failed. Please try again.'
        }), 500

@auth_bp.route('/register-external', methods=['POST'])
def register_external():
    """Register external users with additional fields like Aadhar card"""
    try:
        # Check if request is multipart (with file) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            profile_photo = request.files.get('profile_photo')
        else:
            data = request.get_json()
            profile_photo = None
        
        # Validate required fields for external users
        required_fields = ['email', 'first_name', 'last_name', 'aadhar_card', 'phone', 'profession', 'institution', 'address', 'pincode', 'city', 'state']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False, 
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400

        # Validate Aadhar card format (12 digits)
        aadhar = data['aadhar_card'].replace(' ', '').replace('-', '')
        if not aadhar.isdigit() or len(aadhar) != 12:
            return jsonify({
                'success': False, 
                'message': 'Aadhar card number must be 12 digits'
            }), 400

        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False, 
                'message': 'Email already registered'
            }), 400

        # Check if Aadhar card already exists
        existing_aadhar = User.query.filter_by(aadhar_card=aadhar).first()
        if existing_aadhar:
            return jsonify({
                'success': False, 
                'message': 'Aadhar card number already registered'
            }), 400

        # Handle profile photo upload
        photo_filename = None
        if profile_photo and profile_photo.filename:
            if not allowed_image_file(profile_photo.filename):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image file type. Only JPG, JPEG, and PNG are allowed'
                }), 400
            
            # Check file size (2MB limit)
            profile_photo.seek(0, os.SEEK_END)
            file_size = profile_photo.tell()
            profile_photo.seek(0)
            if file_size > 2 * 1024 * 1024:
                return jsonify({
                    'success': False,
                    'message': 'Profile photo must be less than 2MB'
                }), 400
            
            # Generate secure filename
            filename = secure_filename(profile_photo.filename)
            timestamp = int(datetime.utcnow().timestamp())
            name, ext = os.path.splitext(filename)
            photo_filename = f"profile_{timestamp}_{name}{ext}"
            
            # Ensure upload directory exists
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            save_path = os.path.join(upload_dir, photo_filename)
            profile_photo.save(save_path)
        
        # Generate unique user ID for external users: EXT<NNNNNN>
        prefix = "EXT"
        last_user = (
            User.query
                .filter(User.student_id.like(f"{prefix}%"))
                .order_by(User.student_id.desc())
                .first()
        )
        next_seq = 1
        if last_user and last_user.student_id:
            try:
                digits = ''.join([c for c in last_user.student_id if c.isdigit()])
                last_seq = int(digits) if digits else 0
                next_seq = last_seq + 1
            except Exception:
                next_seq = 1

        # Create new external user
        new_user = User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=RoleEnum.external,
            student_id=f"{prefix}{next_seq:06d}",
            phone=data['phone'],
            aadhar_card=aadhar,
            profession=data['profession'],
            institution=data['institution'],
            address=data['address'],
            pincode=data['pincode'],
            city=data['city'],
            state=data['state'],
            profile_photo=photo_filename,
            is_active=True
        )

        # Generate password for external users
        raw_password = f"{data['first_name'][:3].lower()}{data['phone'][-3:]}{aadhar[-3:]}"
        new_user.set_password(raw_password)
        
        # Save to database with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.session.add(new_user)
                db.session.commit()
                break  # Success, exit retry loop
            except Exception as e:
                db.session.rollback()
                logger.warning(f"Database attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Database error during external user creation after {max_retries} attempts: {e}")
                    return jsonify({
                        'success': False, 
                        'message': 'Database error. Please try again.'
                    }), 500
                time.sleep(0.5)  # Wait before retry

        # Send welcome/credentials email for external users
        try:
            sent = EmailService().send_welcome_email(new_user, raw_password)
            if not sent:
                logger.warning("SMTP not configured or send failed; returning temp password in response for development use")
        except Exception as _e:
            logger.warning(f"Credential email send failed for {new_user.email}: {_e}")

        # Log registration
        log_user_action(
            action='create',
            resource_type='user',
            resource_id=new_user.id,
            details={'registration_method': 'external_registration', 'role': 'external'}
        )
        
        logger.info(f"New external user registered: {data['email']} (ID: {new_user.id})")
        
        response_data = {
            'success': True,
            'message': 'External user registered successfully',
            'data': {
                'user_id': new_user.student_id,
                'email': new_user.email,
                'temporary_password': raw_password
            }
        }

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"External registration error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'External registration failed. Please try again.'
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
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()

        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current password and new password are required'
            }), 400

        # Verify current password
        logger.info(f"Password change attempt by user: {current_user.email}")
        logger.info(f"Current password received: '{current_password}'")
        logger.info(f"Current password length: {len(current_password)}")
        logger.info(f"Current password type: {type(current_password)}")
        logger.info(f"Password hash stored: {current_user.password_hash[:50]}...")
        
        password_check_result = current_user.check_password(current_password)
        logger.info(f"Password check result: {password_check_result}")
        
        if not password_check_result:
            logger.warning(f"Incorrect password attempt for user: {current_user.email}")
            # Try to understand why it failed
            logger.info(f"Testing with stripped password...")
            test_result = current_user.check_password(current_password.strip())
            logger.info(f"Stripped password result: {test_result}")
            
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400

        # Validate new password
        validate_password_strength(new_password)

        # Update password
        logger.info(f"Setting new password for user: {current_user.email}")
        logger.info(f"Before update - is_temp_password: {current_user.is_temp_password}")
        
        current_user.set_password(new_password)
        current_user.is_temp_password = False
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"After update - is_temp_password: {current_user.is_temp_password}")
        logger.info(f"Database committed successfully")

        # Log password change
        log_user_action(
            action='update',
            resource_type='user',
            resource_id=current_user.id,
            details={'action': 'password_change'}
        )

        logger.info(f"Password changed for user: {current_user.email}")

        # Send password change notification email
        try:
            send_password_change_notification(current_user.email, current_user.full_name)
        except Exception as e:
            logger.error(f"Failed to send password change notification: {str(e)}")
            # Don't fail the password change if email fails

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

@auth_bp.route('/forgot-password/send-otp', methods=['POST'])
def send_forgot_password_otp():
    """Send OTP for password reset"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email address is required'
            }), 400
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'No account found with this email address'
            }), 404
        
        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in session with expiry (5 minutes)
        session['forgot_password_otp'] = otp
        session['forgot_password_email'] = email
        session['forgot_password_expires'] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        
        # Send OTP via email
        try:
            send_otp_email(email, user.full_name, otp)
            logger.info(f"Password reset OTP sent to: {email}")
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your email'
            })
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to send verification code. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to process request'
        }), 500

@auth_bp.route('/forgot-password/verify-otp', methods=['POST'])
def verify_forgot_password_otp():
    """Verify OTP for password reset"""
    try:
        data = request.get_json()
        otp = data.get('otp', '').strip()
        
        if not otp:
            return jsonify({
                'success': False,
                'message': 'Verification code is required'
            }), 400
        
        # Check if OTP exists in session
        stored_otp = session.get('forgot_password_otp')
        stored_email = session.get('forgot_password_email')
        expires_str = session.get('forgot_password_expires')
        
        if not stored_otp or not stored_email or not expires_str:
            return jsonify({
                'success': False,
                'message': 'No verification code found. Please request a new one.'
            }), 400
        
        # Check if OTP expired
        expires = datetime.fromisoformat(expires_str)
        if datetime.utcnow() > expires:
            # Clear expired OTP
            session.pop('forgot_password_otp', None)
            session.pop('forgot_password_email', None)
            session.pop('forgot_password_expires', None)
            
            return jsonify({
                'success': False,
                'message': 'Verification code has expired. Please request a new one.'
            }), 400
        
        # Verify OTP
        if otp != stored_otp:
            return jsonify({
                'success': False,
                'message': 'Invalid verification code'
            }), 400
        
        # OTP verified successfully
        session['forgot_password_verified'] = True
        logger.info(f"Password reset OTP verified for: {stored_email}")
        
        return jsonify({
            'success': True,
            'message': 'Verification code confirmed'
        })
        
    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to verify code'
        }), 500

@auth_bp.route('/forgot-password/reset', methods=['POST'])
def reset_forgotten_password():
    """Reset password after OTP verification"""
    try:
        data = request.get_json()
        new_password = data.get('new_password', '').strip()
        
        if not new_password:
            return jsonify({
                'success': False,
                'message': 'New password is required'
            }), 400
        
        # Check if OTP was verified
        if not session.get('forgot_password_verified'):
            return jsonify({
                'success': False,
                'message': 'Please verify your email first'
            }), 400
        
        stored_email = session.get('forgot_password_email')
        if not stored_email:
            return jsonify({
                'success': False,
                'message': 'Session expired. Please start over.'
            }), 400
        
        # Validate new password
        validate_password_strength(new_password)
        
        # Find user and update password
        user = User.query.filter_by(email=stored_email).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Update password
        user.set_password(new_password)
        user.is_temp_password = False  # Mark as permanent password
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Clear session data
        session.pop('forgot_password_otp', None)
        session.pop('forgot_password_email', None)
        session.pop('forgot_password_expires', None)
        session.pop('forgot_password_verified', None)
        
        # Log password reset
        log_user_action(
            action='update',
            resource_type='user',
            resource_id=user.id,
            details={'action': 'password_reset_via_otp'}
        )
        
        logger.info(f"Password reset completed for user: {user.email}")
        
        # Send password change notification email
        try:
            send_password_change_notification(user.email, user.full_name, reset_type="forgot_password")
        except Exception as e:
            logger.error(f"Failed to send password reset notification: {str(e)}")
            # Don't fail the password reset if email fails
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': e.message,
            'field': e.field
        }), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to reset password'
        }), 500

def send_otp_email(email, full_name, otp):
    """Send OTP email to user"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Email configuration from config
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_username = current_app.config.get('SMTP_USERNAME')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    from_email = current_app.config.get('FROM_EMAIL')
    from_name = current_app.config.get('FROM_NAME')
    
    if not all([smtp_server, smtp_port, smtp_username, smtp_password, from_email]):
        raise Exception("Email configuration is incomplete")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = email
    msg['Subject'] = "Password Reset Verification Code - METIS Lab"
    
    # Email body
    body = f"""
    Dear {full_name},
    
    You have requested to reset your password for your METIS Lab account.
    
    Your verification code is: {otp}
    
    This code will expire in 5 minutes for security reasons.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    METIS Lab Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    text = msg.as_string()
    server.sendmail(from_email, email, text)
    server.quit()

def send_password_change_notification(email, full_name, reset_type="manual"):
    """Send password change notification email to user"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Email configuration from config
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT')
    smtp_username = current_app.config.get('SMTP_USERNAME')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    from_email = current_app.config.get('FROM_EMAIL')
    from_name = current_app.config.get('FROM_NAME')
    
    if not all([smtp_server, smtp_port, smtp_username, smtp_password, from_email]):
        raise Exception("Email configuration is incomplete")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = email
    
    # Different subject and content based on reset type
    if reset_type == "forgot_password":
        msg['Subject'] = "Password Successfully Reset - METIS Lab"
        action_text = "reset via email verification"
        security_note = "This reset was completed using the verification code sent to this email address."
    else:
        msg['Subject'] = "Password Changed Successfully - METIS Lab"
        action_text = "changed from your account dashboard"
        security_note = "This change was made while you were logged into your account."
    
    # Get current timestamp
    change_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Email body
    body = f"""
    Dear {full_name},
    
    This email confirms that your METIS Lab account password has been successfully {action_text}.
    
    Details:
    • Account: {email}
    • Date & Time: {change_time}
    • Action: Password {reset_type.replace('_', ' ').title()}
    
    {security_note}
    
    If you did not make this change, please contact our support team immediately or use the "Forgot Password" feature to secure your account.
    
    For your security:
    • Never share your password with anyone
    • Use a strong, unique password
    • Log out from shared devices
    
    If you have any questions or concerns, please don't hesitate to contact us.
    
    Best regards,
    METIS Lab Security Team
    
    ---
    This is an automated security notification. Please do not reply to this email.
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    text = msg.as_string()
    server.sendmail(from_email, email, text)
    server.quit()

@auth_bp.route('/test-route', methods=['GET', 'POST'])
def test_route():
    """Test route to verify Flask is loading new routes"""
    return jsonify({'success': True, 'message': 'Test route working'})

@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        
        # External user fields
        profession = request.form.get('profession', '').strip()
        institution = request.form.get('institution', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        
        # Validate required fields
        if not first_name or not last_name:
            return jsonify({
                'success': False,
                'message': 'First name and last name are required'
            }), 400
        
        # Handle profile photo upload
        profile_photo_filename = None
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generate secure filename
                    filename = secure_filename(f"profile_{current_user.id}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
                    
                    # Save file
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Delete old profile photo if exists
                    if current_user.profile_photo:
                        old_file_path = os.path.join(upload_folder, current_user.profile_photo)
                        if os.path.exists(old_file_path):
                            try:
                                os.remove(old_file_path)
                            except Exception as e:
                                logger.warning(f"Could not delete old profile photo: {str(e)}")
                    
                    profile_photo_filename = filename
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid file type. Please upload PNG, JPG, JPEG, or GIF files only.'
                    }), 400
        
        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.phone = phone if phone else None
        current_user.department = department if department else None
        
        # Update profile photo if uploaded
        if profile_photo_filename:
            current_user.profile_photo = profile_photo_filename
        
        # Update external user fields if applicable
        if current_user.role.value == 'external':
            current_user.profession = profession if profession else None
            current_user.institution = institution if institution else None
            current_user.address = address if address else None
            current_user.city = city if city else None
            current_user.state = state if state else None
            current_user.pincode = pincode if pincode else None
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log profile update
        log_user_action(
            action='update',
            resource_type='user',
            resource_id=current_user.id,
            details={'action': 'profile_update', 'fields_updated': list(request.form.keys())}
        )
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
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

@auth_bp.route('/profile-photo/<filename>', methods=['GET'])
def get_profile_photo(filename):
    """Serve user profile photos"""
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_dir, filename)
    except Exception as e:
        logger.error(f"Profile photo retrieval error: {str(e)}")
        # Return a default avatar or 404
        return jsonify({'success': False, 'message': 'Photo not found'}), 404
