"""
Migration script to add gender column to employees_core table.
"""
import sys
import os

# Add the app directory to path
sys.path.insert(0, '.')

# Import Flask app
from app import app

# Use the app context
with app.app_context():
    from models.db import get_db
    from mysql.connector import Error
    
    try:
        # Get a connection
        db = get_db()
        cur = db.cursor()
        
        # Check current columns in employees_core
        cur.execute("DESCRIBE employees_core")
        columns = {row[0] for row in cur.fetchall()}
        
        # Write to file
        with open('migration_output.txt', 'w') as f:
            f.write(f"Current columns: {columns}\n")
            
            # Add gender column if not exists
            if 'gender' not in columns:
                try:
                    cur.execute("ALTER TABLE employees_core ADD COLUMN gender VARCHAR(50) DEFAULT 'Prefer not to say'")
                    db.commit()
                    f.write("Added column: gender\n")
                except Error as e:
                    f.write(f"Error adding gender: {e}\n")
            else:
                f.write("Column gender already exists\n")
            
            f.write("Migration complete!\n")
        
        cur.close()
        
    except Exception as e:
        with open('migration_output.txt', 'w') as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())