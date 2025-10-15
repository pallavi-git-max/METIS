"""
Migration script to add guide_email column to project_requests table
Run this script to update the database schema
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from backend.models import db
from sqlalchemy import text

def add_guide_email_column():
    """Add guide_email column to project_requests table"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('project_requests')]
            
            if 'guide_email' in columns:
                print("✅ Column 'guide_email' already exists in project_requests table")
                return
            
            # Add the new column
            print("Adding 'guide_email' column to project_requests table...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE project_requests ADD COLUMN guide_email VARCHAR(255)"
                ))
                conn.commit()
            
            print("✅ Successfully added 'guide_email' column to project_requests table")
            print("   - Column type: VARCHAR(255)")
            print("   - Nullable: Yes")
            print("   - Description: Email address of the project guide/mentor")
            
        except Exception as e:
            print(f"❌ Error adding column: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add guide_email column")
    print("=" * 60)
    add_guide_email_column()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
