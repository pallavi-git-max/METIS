#!/usr/bin/env python3
"""
Simple dependency installer for METIS Lab Backend
This script installs only the essential dependencies needed to run the application.
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a single package"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚀 METIS Lab Backend - Essential Dependencies Installer")
    print("=" * 60)
    
    # Essential packages only (avoiding problematic ones)
    essential_packages = [
        "Flask==2.3.2",
        "Flask-Login==0.6.2", 
        "Flask-WTF==1.1.1",
        "Flask-Migrate==4.0.4",
        "Flask-SQLAlchemy==3.0.3",
        "Flask-CORS==4.0.0",
        "SQLAlchemy==2.0.19",
        "WTForms==3.0.1",
        "email-validator==2.0.0",
        "bcrypt==4.0.1",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "python-dateutil==2.8.2"
    ]
    
    print(f"Installing {len(essential_packages)} essential packages...")
    print()
    
    success_count = 0
    failed_packages = []
    
    for package in essential_packages:
        if install_package(package):
            success_count += 1
        else:
            failed_packages.append(package)
        print()
    
    print("=" * 60)
    print(f"Installation Summary:")
    print(f"✅ Successfully installed: {success_count}/{len(essential_packages)} packages")
    
    if failed_packages:
        print(f"❌ Failed to install: {len(failed_packages)} packages")
        print("Failed packages:")
        for package in failed_packages:
            print(f"  - {package}")
        print()
        print("You can try installing these manually:")
        for package in failed_packages:
            print(f"  pip install {package}")
    else:
        print("🎉 All essential packages installed successfully!")
        print()
        print("Next steps:")
        print("1. Create a .env file with your configuration")
        print("2. Run: flask db init")
        print("3. Run: flask db migrate -m 'Initial migration'")
        print("4. Run: flask db upgrade")
        print("5. Run: python app.py")

if __name__ == "__main__":
    main()
