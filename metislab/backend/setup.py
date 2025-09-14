#!/usr/bin/env python3
"""
Setup script for METIS Lab Admin Dashboard Backend
This script helps set up the development environment and install dependencies.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    venv_path = "venv"
    if os.path.exists(venv_path):
        print("Virtual environment already exists")
        return True
    
    return run_command(f"python -m venv {venv_path}", "Creating virtual environment")

def activate_virtual_environment():
    """Get activation command for virtual environment"""
    system = platform.system().lower()
    if system == "windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def install_dependencies():
    """Install Python dependencies"""
    # Upgrade pip first
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = ".env"
    if os.path.exists(env_file):
        print("📄 .env file already exists")
        return True
    
    print("📄 Creating .env file...")
    env_content = """# METIS Lab Admin Dashboard Configuration

# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///metis_portal.db
# For PostgreSQL: DATABASE_URL=postgresql://username:password@localhost/metis_portal

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Security Configuration
REMEMBER_COOKIE_DURATION=3600

# Logging Configuration
LOG_LEVEL=INFO

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@metislab.edu
FROM_NAME=METIS Lab
BASE_URL=http://localhost:5000
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'logs', 'migrations']
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"📁 Created directory: {directory}")
            except Exception as e:
                print(f"❌ Failed to create directory {directory}: {e}")
                return False
        else:
            print(f"📁 Directory already exists: {directory}")
    
    return True

def initialize_database():
    """Initialize database with migrations"""
    commands = [
        ("flask db init", "Initializing database migrations"),
        ("flask db migrate -m 'Initial migration'", "Creating initial migration"),
        ("flask db upgrade", "Applying database migrations")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  {description} failed, but continuing...")
    
    return True

def main():
    """Main setup function"""
    print("🚀 METIS Lab Admin Dashboard Backend Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Setup failed at virtual environment creation")
        sys.exit(1)
    
    # Create necessary directories
    if not create_directories():
        print("❌ Setup failed at directory creation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Setup failed at .env file creation")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("❌ Setup failed at database initialization")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print(f"1. Activate virtual environment: {activate_virtual_environment()}")
    print("2. Update .env file with your configuration")
    print("3. Run the application: python app.py")
    print("4. Access the admin dashboard at: http://localhost:5000/admin/dashboard")
    
    print("\n🔧 Development commands:")
    print("- Run tests: pytest")
    print("- Format code: black .")
    print("- Lint code: flake8")
    print("- Create migration: flask db migrate -m 'description'")
    print("- Apply migration: flask db upgrade")

if __name__ == "__main__":
    main()
