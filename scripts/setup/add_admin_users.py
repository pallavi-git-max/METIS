#!/usr/bin/env python3
"""
Simple script to add admin users to the database
Run this directly to create the admin users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum

def add_admin_users():
    """Add admin users to the database"""
    app = create_app()
    
    with app.app_context():
        # Admin users to create with specific roles
        admin_users = [
            {
                'email': 'guide@metislab.edu',
                'first_name': 'Project',
                'last_name': 'Guide',
                'password': 'Guide@2024!',
                'student_id': 'GUIDE001',
                'phone': '9876543210',
                'department': 'Administration',
                'designation': 'Project Guide',
                'role': RoleEnum.project_guide
            },
            {
                'email': 'hod@metislab.edu',
                'first_name': 'Head',
                'last_name': 'Department',
                'password': 'HOD@2024!',
                'student_id': 'HOD001',
                'phone': '9876543212',
                'department': 'Administration',
                'designation': 'Head of Department',
                'role': RoleEnum.hod
            },
            {
                'email': 'itservices@metislab.edu',
                'first_name': 'IT',
                'last_name': 'Services',
                'password': 'ITServices@2024!',
                'student_id': 'IT001',
                'phone': '9876543213',
                'department': 'IT Services',
                'designation': 'IT Services Manager',
                'role': RoleEnum.it_services
            },
            {
                'email': 'admin@metislab.edu',
                'first_name': 'System',
                'last_name': 'Admin',
                'password': 'Admin@2024!',
                'student_id': 'ADMIN001',
                'phone': '9876543214',
                'department': 'Administration',
                'designation': 'System Administrator',
                'role': RoleEnum.admin
            }
        ]
        
        print("Adding admin users to database...")
        print("=" * 50)
        
        for user_data in admin_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"User {user_data['email']} already exists - skipping")
                continue
            
            # Create new user
            user = User(
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                department=user_data['department'],
                student_id=user_data['student_id'],
                phone=user_data['phone'],
                designation=user_data['designation'],
                is_active=True
            )
            user.set_password(user_data['password'])
            
            db.session.add(user)
            print(f"Created user: {user_data['email']}")
        
        # Commit all changes
        db.session.commit()
        print("=" * 50)
        print("Admin users added successfully!")
        print("\nLogin credentials:")
        print("-" * 30)
        for user_data in admin_users:
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print(f"Student ID: {user_data['student_id']}")
            print("-" * 30)

if __name__ == "__main__":
    try:
        add_admin_users()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Flask app is properly configured and database is accessible.")

