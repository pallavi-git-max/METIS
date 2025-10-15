"""
Migration script to add is_temp_password column to users table
Run this script to update existing database
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
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'is_temp_password' in column_names:
        print("✓ is_temp_password column already exists in users table")
    else:
        print("Adding is_temp_password column to users table...")
        
        # Add the column with default value True for new users
        cursor.execute("ALTER TABLE users ADD COLUMN is_temp_password BOOLEAN DEFAULT 1")
        conn.commit()
        
        print("✓ Successfully added is_temp_password column")
        
        # Smart update: Set is_temp_password=False for users whose updated_at != created_at
        # This indicates they've likely already changed their password
        cursor.execute("""
            UPDATE users 
            SET is_temp_password = 0 
            WHERE updated_at IS NOT NULL 
            AND created_at IS NOT NULL 
            AND datetime(updated_at) > datetime(created_at)
        """)
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"\n✓ Set is_temp_password=False for {updated_count} users who already updated their accounts")
        
        # Count remaining users with temp passwords
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_temp_password = 1")
        temp_pass_count = cursor.fetchone()[0]
        
        print(f"✓ {temp_pass_count} users still have temporary passwords and will be prompted to change")
    
    conn.close()
    print("\nMigration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {str(e)}")
    if conn:
        conn.rollback()
        conn.close()
