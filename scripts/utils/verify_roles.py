"""Verify all roles in the database"""
from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum

app = create_app()

with app.app_context():
    print("\n=== ROLE ENUM VERIFICATION ===")
    print("Available roles in RoleEnum:")
    for role in RoleEnum:
        print(f"  - {role.value}")
    
    print("\n=== ALL USERS IN DATABASE ===")
    users = User.query.all()
    for user in users:
        print(f"Email: {user.email:40} | Role: {user.role.value:20} | Active: {user.is_active}")
    
    print("\n=== ADMIN PORTAL USERS (project_guide, hod, it_services, admin) ===")
    admin_roles = [RoleEnum.project_guide, RoleEnum.hod, RoleEnum.it_services, RoleEnum.admin]
    admin_users = User.query.filter(User.role.in_(admin_roles)).all()
    for user in admin_users:
        print(f"Email: {user.email:40} | Role: {user.role.value:20} | Name: {user.full_name}")
    
    print("\n=== IT SERVICES USER CHECK ===")
    it_services_users = User.query.filter_by(role=RoleEnum.it_services).all()
    if it_services_users:
        for user in it_services_users:
            print(f"✓ IT Services user found:")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.full_name}")
            print(f"  Role: {user.role.value}")
            print(f"  Active: {user.is_active}")
    else:
        print("✗ No IT Services users found in database!")
    
    print("\n=== SUMMARY ===")
    print(f"Total users: {User.query.count()}")
    for role in RoleEnum:
        count = User.query.filter_by(role=role).count()
        print(f"{role.value}: {count} user(s)")
