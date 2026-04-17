"""
Database seeder — run ONCE after creating tables.
  python seed_db.py
"""
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import date
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB = {
    'host':     os.getenv('DB_HOST', 'mysql.railway.internal'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'railway'),
    'port':     int(os.getenv('DB_PORT', 3306)),
}
DATABASE_URL = os.getenv('DATABASE_URL')

def parse_database_url(database_url):
    """Parse MySQL connection URL."""
    if database_url.startswith('mysql://'):
        database_url = database_url.replace('mysql://', '')
    
    if '@' in database_url:
        credentials, host_db = database_url.split('@')
        user, password = credentials.split(':')
    else:
        return None
    
    if '/' in host_db:
        host_port, database = host_db.split('/')
    else:
        host_port = host_db
        database = 'railway'
    
    if ':' in host_port:
        host, port = host_port.split(':')
        port = int(port)
    else:
        host = host_port
        port = 3306
    
    return {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port,
    }

def hp(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def run():
    if DATABASE_URL:
        conn_args = parse_database_url(DATABASE_URL)
        conn = mysql.connector.connect(**conn_args)
    else:
        conn = mysql.connector.connect(**DB)
    cur  = conn.cursor()

    try:
        # 1 — Company
        cur.execute("""
            INSERT IGNORE INTO companies (id, name, industry, address, phone, email, website)
            VALUES (1,'TechCorp Inc.','Technology','123 Silicon Valley','555-0100',
                    'hr@techcorp.com','www.techcorp.com')
        """)

        # 2 — Departments
        depts = [
            (1,'Human Resources','People operations'),
            (1,'Engineering','Software development'),
            (1,'Finance','Accounting'),
            (1,'Sales','Revenue'),
            (1,'Operations','Daily operations'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO departments (company_id,name,description)
            VALUES(%s,%s,%s)
        """, depts)

        # 3 — Users
        users = [
            (1,'admin',    hp('Admin@123'),   'admin@techcorp.com',      'System Administrator','Admin'),
            (1,'hr_manager',hp('HR@123456'),  'hrmanager@techcorp.com',  'Sarah Johnson',       'HR'),
            (1,'chro',     hp('CHRO@1234'),   'chro@techcorp.com',       'Michael Chen',        'CHRO'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO users
              (company_id,username,password_hash,email,full_name,role)
            VALUES(%s,%s,%s,%s,%s,%s)
        """, users)

        # 4 — Employees (reduced to match schema)
        employees = [
            (1,'EMP001','John','Smith','john@tech.com','555-0101',2,'Developer','Full-Time','Active','2022-03-15'),
            (1,'EMP002','Emily','Davis','emily@tech.com','555-0102',2,'Developer','Full-Time','Active','2023-01-10'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO employees_core
              (company_id,employee_code,first_name,last_name,email,phone,
               department_id,job_title,employment_type,status,hire_date)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, employees)

        # 5 — Leave balances
        yr = date.today().year
        for eid in range(1, 3):
            cur.execute("""
                INSERT IGNORE INTO leave_balances
                  (company_id,employee_id,year,annual_total,annual_used)
                VALUES(%s,%s,%s,21,%s)
            """, (1, eid, yr, random.randint(0,10)))

        conn.commit()
        print("✅ Database seeded successfully!")

    except Error as exc:
        conn.rollback()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()