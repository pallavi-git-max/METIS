"""
Migration script to add profile_photo column to users table
Run this script once to update existing database
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'metis_portal.db')

print(f"Connecting to database: {db_path}")

if not os.path.exists(db_path):
    print("Database not found. It will be created when you run the application.")
    exit(0)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'profile_photo' in columns:
        print("✓ profile_photo column already exists in users table")
    else:
        print("Adding profile_photo column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo VARCHAR(255)")
        conn.commit()
        print("✓ Successfully added profile_photo column")
    
    conn.close()
    print("\nMigration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {str(e)}")
    if conn:
        conn.close()
