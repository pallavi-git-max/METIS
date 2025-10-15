"""
Script to remove all lab_incharge users from the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from backend.models import db, User
from sqlalchemy import text

def remove_lab_incharge_users():
    """Remove or convert all lab_incharge users"""
    with app.app_context():
        try:
            # Check if there is a user with email labincharge@metislab.edu
            result = db.session.execute(text(
                "SELECT id, email, first_name, last_name, role FROM users WHERE email = 'labincharge@metislab.edu'"
            ))
            lab_incharge_users = result.fetchall()
            
            if not lab_incharge_users:
                print("✅ No lab_incharge users found in database")
                return
            
            print(f"Found {len(lab_incharge_users)} lab_incharge user(s) to delete:")
            for user in lab_incharge_users:
                print(f"  - {user.first_name} {user.last_name} ({user.email}) - Role: {user.role}")
            
            # Delete users with email labincharge@metislab.edu
            print("\nDeleting lab_incharge user account...")
            db.session.execute(text(
                "DELETE FROM users WHERE email = 'labincharge@metislab.edu'"
            ))
            db.session.commit()
            
            print("✅ Successfully deleted lab_incharge user account")
            print("   The user can no longer log in.")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Removing Lab Incharge Users")
    print("=" * 60)
    remove_lab_incharge_users()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
