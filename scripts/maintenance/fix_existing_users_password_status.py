"""
Script to fix is_temp_password status for existing users
Run this to mark users who already changed passwords as is_temp_password=False
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'metis_portal.db')

print(f"Connecting to database: {db_path}")

if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current status
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_temp_password = 1")
    temp_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_temp_password = 0")
    changed_count = cursor.fetchone()[0]
    
    print(f"\nCurrent Status:")
    print(f"  Users with temporary passwords: {temp_count}")
    print(f"  Users who changed passwords: {changed_count}")
    
    # Update users whose updated_at > created_at (they've made changes)
    print("\nUpdating users who already changed their passwords...")
    
    cursor.execute("""
        UPDATE users 
        SET is_temp_password = 0 
        WHERE updated_at IS NOT NULL 
        AND created_at IS NOT NULL 
        AND datetime(updated_at) > datetime(created_at)
        AND is_temp_password = 1
    """)
    
    updated = cursor.rowcount
    conn.commit()
    
    print(f"✓ Updated {updated} users to is_temp_password=False")
    
    # Show updated status
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_temp_password = 1")
    temp_count_after = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_temp_password = 0")
    changed_count_after = cursor.fetchone()[0]
    
    print(f"\nUpdated Status:")
    print(f"  Users with temporary passwords: {temp_count_after}")
    print(f"  Users who changed passwords: {changed_count_after}")
    
    # Show users who still have temp passwords
    if temp_count_after > 0:
        print(f"\nUsers still with temporary passwords:")
        cursor.execute("""
            SELECT email, first_name, last_name, created_at 
            FROM users 
            WHERE is_temp_password = 1
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        for user in users:
            print(f"  - {user[1]} {user[2]} ({user[0]}) - Created: {user[3]}")
    
    conn.close()
    print("\n✓ Fix completed successfully!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    if conn:
        conn.rollback()
        conn.close()
