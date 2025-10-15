#!/usr/bin/env python3
"""
Initialize database with admin users
Run this script to set up the database with all required users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum

def init_database():
    """Initialize database with all users"""
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created/verified")
        
        # Create admin users
        admin_users = [
            {
                'email': 'admin@metislab.edu',
                'first_name': 'Admin',
                'last_name': 'User',
                'password': 'Admin@123456',
                'student_id': 'ADMIN001',
                'phone': '9876543200',
                'designation': 'System Administrator'
            },
            {
                'email': 'guide@metislab.edu',
                'first_name': 'Guide',
                'last_name': 'Admin',
                'password': 'Guide@2024!',
                'student_id': 'GUIDE001',
                'phone': '9876543210',
                'designation': 'Project Guide'
            },
            {
                'email': 'hod@metislab.edu',
                'first_name': 'HOD',
                'last_name': 'Admin',
                'password': 'HOD@2024!',
                'student_id': 'HOD001',
                'phone': '9876543211',
                'designation': 'Head of Department'
            },
            {
                'email': 'itservice@metislab.edu',
                'first_name': 'IT',
                'last_name': 'Service',
                'password': 'ITService@2024!',
                'student_id': 'IT001',
                'phone': '9876543212',
                'designation': 'IT Service Manager'
            },
            {
                'email': 'metisincharge@metislab.edu',
                'first_name': 'METIS',
                'last_name': 'Incharge',
                'password': 'METIS@2024!',
                'student_id': 'METIS001',
                'phone': '9876543213',
                'designation': 'METIS Lab Incharge'
            }
        ]
        
        # Create test users
        test_users = [
            {
                'email': 'student1@metislab.edu',
                'first_name': 'Student',
                'last_name': 'One',
                'password': 'Student@123456',
                'student_id': 'S123456',
                'phone': '9999999999',
                'designation': 'Student',
                'role': RoleEnum.student
            },
            {
                'email': 'faculty1@metislab.edu',
                'first_name': 'Faculty',
                'last_name': 'One',
                'password': 'Faculty@123456',
                'student_id': 'F123456',
                'phone': '9999999998',
                'designation': 'Faculty',
                'role': RoleEnum.faculty
            }
        ]
        
        print("Creating users...")
        print("=" * 50)
        
        # Add admin users
        for user_data in admin_users:
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"Admin user {user_data['email']} already exists")
                continue
            
            user = User(
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=RoleEnum.admin,
                student_id=user_data['student_id'],
                phone=user_data['phone'],
                designation=user_data['designation'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"Created admin: {user_data['email']}")
        
        # Add test users
        for user_data in test_users:
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"Test user {user_data['email']} already exists")
                continue
            
            user = User(
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                student_id=user_data['student_id'],
                phone=user_data['phone'],
                designation=user_data['designation'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"Created test user: {user_data['email']}")
        
        # Commit all changes
        db.session.commit()
        print("=" * 50)
        print("Database initialized successfully!")
        print("\nAdmin Login Credentials:")
        print("-" * 40)
        for user_data in admin_users:
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print(f"Student ID: {user_data['student_id']}")
            print("-" * 40)

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
