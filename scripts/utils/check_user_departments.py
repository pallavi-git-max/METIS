"""
Check department field for all users
"""
from app import create_app
from backend.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    
    print(f"\n{'='*80}")
    print(f"USER DEPARTMENT STATUS REPORT")
    print(f"{'='*80}")
    
    users_with_dept = []
    users_without_dept = []
    
    for user in users:
        print(f"\nUser: {user.full_name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role.value}")
        print(f"Department: '{user.department}' (Type: {type(user.department)})")
        print(f"Campus: {user.campus.value if user.campus else None}")
        print("-" * 60)
        
        if user.department and user.department.strip():
            users_with_dept.append(user)
        else:
            users_without_dept.append(user)
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  📊 Total Users: {len(users)}")
    print(f"  ✅ Users with Department: {len(users_with_dept)}")
    print(f"  ❌ Users without Department: {len(users_without_dept)}")
    
    if users_without_dept:
        print(f"\n🔍 Users missing department information:")
        for user in users_without_dept:
            print(f"  • {user.full_name} ({user.email}) - Role: {user.role.value}")
    
    print(f"{'='*80}\n")
