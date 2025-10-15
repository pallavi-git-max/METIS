"""
Fix missing department information for users
"""
from app import create_app
from backend.models import User, db

app = create_app()

with app.app_context():
    users = User.query.all()
    
    print(f"\n{'='*80}")
    print(f"FIXING USER DEPARTMENT INFORMATION")
    print(f"{'='*80}")
    
    updated_count = 0
    
    for user in users:
        if not user.department or not user.department.strip():
            # Set default department based on role
            if user.role.value == 'student':
                user.department = 'Computer Science'
            elif user.role.value == 'faculty':
                user.department = 'Computer Science'
            elif user.role.value == 'project_guide':
                user.department = 'Computer Science'
            elif user.role.value == 'lab_incharge':
                user.department = 'Computer Science'
            elif user.role.value == 'hod':
                user.department = 'Computer Science'
            elif user.role.value == 'it_services':
                user.department = 'IT Services'
            elif user.role.value == 'admin':
                user.department = 'Administration'
            elif user.role.value == 'external':
                user.department = 'External'
            else:
                user.department = 'General'
            
            print(f"✅ Updated {user.full_name} ({user.email})")
            print(f"   Role: {user.role.value} → Department: {user.department}")
            updated_count += 1
        else:
            print(f"✓ {user.full_name} already has department: {user.department}")
    
    if updated_count > 0:
        db.session.commit()
        print(f"\n🎉 Successfully updated {updated_count} users with department information!")
    else:
        print(f"\n✅ All users already have department information!")
    
    print(f"\n{'='*80}")
    print(f"VERIFICATION - Current Department Status:")
    print(f"{'='*80}")
    
    for user in users:
        print(f"• {user.full_name}: {user.department}")
    
    print(f"{'='*80}\n")
