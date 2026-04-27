"""
Migration script to add missing columns to company_subscriptions table.
Run this script to fix the 'Unknown column cs.custom_price' error.
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
    
    # Check current columns in company_subscriptions
    cur.execute("DESCRIBE company_subscriptions")
    columns = {row[0] for row in cur.fetchall()}
    
    print(f"Current columns in company_subscriptions: {columns}")
    
    # Add custom_price column
    try:
        cur.execute('ALTER TABLE company_subscriptions ADD COLUMN custom_price DECIMAL(10, 2) DEFAULT NULL')
        print('✓ Added custom_price column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ custom_price column already exists')
        else:
            print(f'✗ custom_price: {e}')

    # Add is_global_free column
    try:
        cur.execute('ALTER TABLE company_subscriptions ADD COLUMN is_global_free BOOLEAN DEFAULT FALSE')
        print('✓ Added is_global_free column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ is_global_free column already exists')
        else:
            print(f'✗ is_global_free: {e}')

    # Add free_access_until column
    try:
        cur.execute('ALTER TABLE company_subscriptions ADD COLUMN free_access_until DATE DEFAULT NULL')
        print('✓ Added free_access_until column')
    except mysql.connector.Error as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print('✓ free_access_until column already exists')
        else:
            print(f'✗ free_access_until: {e}')

    db.commit()
    cur.close()
    db.close()
    print('\n✅ Migration complete!')
    
except mysql.connector.Error as e:
    print(f'Database error: {e}')
    raise