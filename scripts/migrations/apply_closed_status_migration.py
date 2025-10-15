"""
Apply the closed status migration to add closed status functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from backend.models import db
from sqlalchemy import text

def apply_migration():
    """Apply closed status migration"""
    with app.app_context():
        try:
            print("=" * 60)
            print("Applying Closed Status Migration")
            print("=" * 60)
            
            # Add closed_at column
            print("\n1. Adding closed_at column...")
            try:
                db.session.execute(text(
                    "ALTER TABLE project_requests ADD COLUMN closed_at DATETIME"
                ))
                print("   ✓ closed_at column added")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ✓ closed_at column already exists")
                else:
                    raise
            
            # Add closed_by column
            print("\n2. Adding closed_by column...")
            try:
                db.session.execute(text(
                    "ALTER TABLE project_requests ADD COLUMN closed_by INTEGER"
                ))
                print("   ✓ closed_by column added")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ✓ closed_by column already exists")
                else:
                    raise
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ Migration Applied Successfully!")
            print("=" * 60)
            print("\nAdmin users can now close requests using:")
            print("POST /admin/requests/<request_id>/close")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error applying migration: {str(e)}")
            raise

if __name__ == '__main__':
    apply_migration()
