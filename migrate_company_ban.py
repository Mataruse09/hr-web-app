"""
Migration script to add missing columns to companies table.
Run this script to fix the 'Unknown column ban_reason' error.
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Get database connection
def get_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
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
    
    # Check current columns in companies
    cur.execute("DESCRIBE companies")
    columns = {row[0] for row in cur.fetchall()}
    
    print(f"Current columns in companies: {columns}")
    
    # Add ban_reason column
    try:
        cur.execute('ALTER TABLE companies ADD COLUMN ban_reason TEXT DEFAULT NULL')
        print('✓ Added ban_reason column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ ban_reason column already exists')
        else:
            print(f'✗ ban_reason: {e}')

    # Add ban_type column
    try:
        cur.execute('ALTER TABLE companies ADD COLUMN ban_type VARCHAR(50) DEFAULT NULL')
        print('✓ Added ban_type column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ ban_type column already exists')
        else:
            print(f'✗ ban_type: {e}')

    # Add banned_at column
    try:
        cur.execute('ALTER TABLE companies ADD COLUMN banned_at DATETIME DEFAULT NULL')
        print('✓ Added banned_at column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ banned_at column already exists')
        else:
            print(f'✗ banned_at: {e}')

    # Add banned_by column
    try:
        cur.execute('ALTER TABLE companies ADD COLUMN banned_by INT DEFAULT NULL')
        print('✓ Added banned_by column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ banned_by column already exists')
        else:
            print(f'✗ banned_by: {e}')

    db.commit()
    cur.close()
    db.close()
    print('\n✅ Migration complete!')
    
except mysql.connector.Error as e:
    print(f'Database error: {e}')
    raise