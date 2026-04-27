"""
Migration script to add gender column to employees_core table.
Run this script to fix the missing gender column error.
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Get database connection
def get_connection():
    # Try DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Parse mysql://user:password@host:port/database
        url = database_url.replace('mysql://', '')
        credentials, host_db = url.split('@')
        user, password = credentials.split(':')
        host_port, database = host_db.split('/')
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 3306
    else:
        host = os.getenv('DB_HOST', 'mysql.railway.internal')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        database = os.getenv('DB_NAME', 'railway')
        port = int(os.getenv('DB_PORT', 3306))
    
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

try:
    db = get_connection()
    cur = db.cursor()
    
    # Check current columns in employees_core
    cur.execute("DESCRIBE employees_core")
    columns = {row[0] for row in cur.fetchall()}
    
    print(f"Current columns in employees_core: {columns}")
    
    # Add gender column if not exists
    if 'gender' not in columns:
        cur.execute("ALTER TABLE employees_core ADD COLUMN gender VARCHAR(50) DEFAULT 'Prefer not to say'")
        db.commit()
        print("Added column: gender")
    else:
        print("Column gender already exists")
    
    print("Migration complete!")
    
    cur.close()
    db.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()