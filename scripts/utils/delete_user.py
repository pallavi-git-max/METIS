"""
Script to delete a specific user from the database
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
    
    email_to_delete = 'vibhah20@gmail.com'
    
    # Check if user exists
    cursor.execute("SELECT id, email, first_name, last_name FROM users WHERE email = ?", (email_to_delete,))
    user = cursor.fetchone()
    
    if user:
        print(f"\nFound user:")
        print(f"  ID: {user[0]}")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]} {user[3]}")
        
        # Delete the user
        cursor.execute("DELETE FROM users WHERE email = ?", (email_to_delete,))
        conn.commit()
        
        print(f"\n✓ Successfully deleted user: {email_to_delete}")
    else:
        print(f"\n✗ User not found: {email_to_delete}")
    
    conn.close()
    print("\nOperation completed!")
    
except Exception as e:
    print(f"Error: {str(e)}")
    if conn:
        conn.rollback()
        conn.close()
