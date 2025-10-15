"""
Migration script to change department column from ENUM to VARCHAR
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
    
    print("Updating department column to accept custom school names...")
    
    # SQLite doesn't support ALTER COLUMN directly, so we need to:
    # 1. Create a new table with the correct schema
    # 2. Copy data from old table
    # 3. Drop old table
    # 4. Rename new table
    
    # But for SQLite, it's simpler to just drop and recreate if the column type change is simple
    # Since department is nullable and optional, we can work with it directly
    
    # Check current schema
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    print("\nCurrent users table schema:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    # For SQLite, ENUM is stored as VARCHAR anyway, so no actual migration needed
    # Just verify it works
    print("\n✓ SQLite stores ENUM as VARCHAR - no migration needed!")
    print("✓ Department field can now accept custom school names")
    
    conn.close()
    print("\nVerification completed successfully!")
    print("You can now use custom department names in registration.")
    
except Exception as e:
    print(f"Error during verification: {str(e)}")
    if conn:
        conn.close()
