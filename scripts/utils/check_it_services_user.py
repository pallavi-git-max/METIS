"""Check IT Services user data"""
from app import create_app
from backend.models import db
from backend.models.user import User, RoleEnum

app = create_app()

with app.app_context():
    print("\n=== IT SERVICES USER DATA ===")
    it_user = User.query.filter_by(email='itservices@metislab.edu').first()
    
    if it_user:
        print(f"Email: {it_user.email}")
        print(f"Name: {it_user.full_name}")
        print(f"Role: {it_user.role} (type: {type(it_user.role)})")
        print(f"Department: {it_user.department} (type: {type(it_user.department)})")
        print(f"Designation: {it_user.designation}")
        print(f"Student ID: {it_user.student_id}")
        print(f"Phone: {it_user.phone}")
        print(f"Active: {it_user.is_active}")
        print(f"Last Login: {it_user.last_login}")
        print(f"Created At: {it_user.created_at}")
        
        print("\n=== Testing department.value ===")
        try:
            if it_user.department:
                dept_value = it_user.department.value
                print(f"✓ department.value works: {dept_value}")
            else:
                print(f"✓ department is None/False")
        except Exception as e:
            print(f"✗ ERROR accessing department.value: {e}")
            print(f"Department raw value: {repr(it_user.department)}")
    else:
        print("IT Services user not found!")
