"""
Check is_temp_password status for a user
"""
from app import create_app
from backend.models import User

app = create_app()

with app.app_context():
    # Check all users and their password status
    users = User.query.all()
    
    temp_password_users = []
    permanent_password_users = []
    
    print(f"\n{'='*80}")
    print(f"PASSWORD STATUS REPORT - ALL USERS")
    print(f"{'='*80}")
    
    for user in users:
        if user.is_temp_password:
            temp_password_users.append(user)
        else:
            permanent_password_users.append(user)
    
    print(f"\n🔐 USERS WITH TEMPORARY PASSWORDS ({len(temp_password_users)}):")
    print("   (These users will see the notification banner)")
    print("-" * 60)
    for user in temp_password_users:
        print(f"   • {user.full_name} ({user.email})")
        print(f"     Created: {user.created_at}")
        print(f"     Last Login: {user.last_login}")
        print()
    
    print(f"✅ USERS WITH PERMANENT PASSWORDS ({len(permanent_password_users)}):")
    print("   (These users will NOT see the banner)")
    print("-" * 60)
    for user in permanent_password_users:
        print(f"   • {user.full_name} ({user.email})")
        print(f"     Last Updated: {user.updated_at}")
        print()
    
    print(f"{'='*80}")
    print(f"SUMMARY:")
    print(f"  📊 Total Users: {len(users)}")
    print(f"  🔐 Need Password Change: {len(temp_password_users)}")
    print(f"  ✅ Already Changed: {len(permanent_password_users)}")
    print(f"{'='*80}\n")
