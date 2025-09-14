import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'metis_portal.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = 3600  # 1 hour in seconds

    # Email Configuration
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@metislab.edu')
    FROM_NAME = os.environ.get('FROM_NAME', 'METIS Lab')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # Security headers can be added here or in after_request hooks
    # For simplicity, we will add a method to apply headers in app.py
