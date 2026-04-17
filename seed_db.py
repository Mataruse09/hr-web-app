"""
Database seeder — run ONCE after creating tables.
  python seed_db.py
"""
import psycopg2
import bcrypt
from datetime import date
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB = {
    'host':     os.getenv('DB_HOST'),
    'user':     os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname':   os.getenv('DB_NAME'),
    'port':     int(os.getenv('DB_PORT', 5432)),
}
DATABASE_URL = os.getenv('DATABASE_URL')

def hp(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def run():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        conn = psycopg2.connect(**DB, sslmode='require')
    cur  = conn.cursor()

    try:
        # 1 — Company
        cur.execute("""
            INSERT INTO companies (id, name, industry, address, phone, email, website)
            VALUES (1,'TechCorp Inc.','Technology','123 Silicon Valley','555-0100',
                    'hr@techcorp.com','www.techcorp.com')
            ON CONFLICT (id) DO NOTHING
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
            INSERT INTO departments (company_id,name,description)
            VALUES(%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, depts)

        # 3 — Users
        users = [
            (1,'admin',    hp('Admin@123'),   'admin@techcorp.com',      'System Administrator','Admin'),
            (1,'hr_manager',hp('HR@123456'),  'hrmanager@techcorp.com',  'Sarah Johnson',       'HR'),
            (1,'chro',     hp('CHRO@1234'),   'chro@techcorp.com',       'Michael Chen',        'CHRO'),
        ]
        cur.executemany("""
            INSERT INTO users
              (company_id,username,password_hash,email,full_name,role)
            VALUES(%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, users)

        # 4 — Employees (reduced to match schema)
        employees = [
            (1,'EMP001','John','Smith','john@tech.com','555-0101',2,'Developer','Full-Time','Active','2022-03-15'),
            (1,'EMP002','Emily','Davis','emily@tech.com','555-0102',2,'Developer','Full-Time','Active','2023-01-10'),
        ]
        cur.executemany("""
            INSERT INTO employees_core
              (company_id,employee_code,first_name,last_name,email,phone,
               department_id,job_title,employment_type,status,hire_date)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, employees)

        # 5 — Leave balances
        yr = date.today().year
        for eid in range(1, 3):
            cur.execute("""
                INSERT INTO leave_balances
                  (company_id,employee_id,year,annual_total,annual_used)
                VALUES(%s,%s,%s,21,%s)
                ON CONFLICT DO NOTHING
            """, (1, eid, yr, random.randint(0,10)))

        conn.commit()
        print("✅ Database seeded successfully!")

    except Exception as exc:
        conn.rollback()
        print(f"❌ Seed failed: {exc}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()