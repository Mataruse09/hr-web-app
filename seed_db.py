"""
Database seeder — run ONCE after creating tables.
  python seed_db.py
"""
import mysql.connector
import bcrypt
from datetime import date
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB = {
    'host':     os.getenv('MYSQL_HOST', 'localhost'),
    'user':     os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'hr_system'),
    'port':     int(os.getenv('MYSQL_PORT', 3306)),
}

def hp(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def run():
    conn = mysql.connector.connect(**DB)
    cur  = conn.cursor()

    try:
        # 1 — Company
        cur.execute("""
            INSERT IGNORE INTO companies (id, name, industry, address, phone, email, website)
            VALUES (1,'TechCorp Inc.','Technology','123 Silicon Valley, CA 94000','555-0100',
                    'hr@techcorp.com','www.techcorp.com')
        """)

        # 2 — Departments
        depts = [
            (1,'Human Resources','People operations and talent management'),
            (1,'Engineering','Software development and infrastructure'),
            (1,'Finance','Accounting, budgeting and financial planning'),
            (1,'Sales & Marketing','Revenue generation and brand strategy'),
            (1,'Operations','Daily operations and process management'),
        ]
        cur.executemany(
            "INSERT IGNORE INTO departments (company_id,name,description) VALUES(%s,%s,%s)", depts
        )

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

        # 4 — Employees
        employees = [
            (1,'EMP001','John',    'Smith',   'john.smith@techcorp.com',  '555-0101',2,'Senior Developer', 'Full-Time','Active','2022-03-15','1990-05-12','Male',  'American'),
            (1,'EMP002','Emily',   'Davis',   'emily.davis@techcorp.com', '555-0102',2,'Junior Developer', 'Full-Time','Active','2023-01-10','1997-08-22','Female','American'),
            (1,'EMP003','Robert',  'Wilson',  'r.wilson@techcorp.com',    '555-0103',3,'Financial Analyst','Full-Time','Active','2021-07-20','1988-11-03','Male',  'British'),
            (1,'EMP004','Jennifer','Brown',   'j.brown@techcorp.com',     '555-0104',4,'Sales Manager',   'Full-Time','Active','2020-11-05','1985-02-17','Female','Canadian'),
            (1,'EMP005','David',   'Taylor',  'd.taylor@techcorp.com',    '555-0105',1,'HR Specialist',   'Full-Time','Active','2022-06-01','1993-07-30','Male',  'American'),
            (1,'EMP006','Amanda',  'Martinez','a.martinez@techcorp.com',  '555-0106',2,'DevOps Engineer', 'Full-Time','Active','2023-03-20','1995-04-15','Female','Mexican'),
            (1,'EMP007','Chris',   'Anderson','c.anderson@techcorp.com',  '555-0107',5,'Ops Manager',     'Full-Time','Active','2021-02-15','1987-09-08','Male',  'Australian'),
            (1,'EMP008','Lisa',    'Thomas',  'l.thomas@techcorp.com',    '555-0108',4,'Marketing Spec.', 'Full-Time','Active','2022-09-12','1994-12-20','Female','American'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO employees_core
              (company_id,employee_code,first_name,last_name,email,phone,
               department_id,job_title,employment_type,status,hire_date,
               date_of_birth,gender,nationality)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, employees)

        # 5 — Compensation
        comp = [
            (1,1, 85000,12000,6000,2400,0, 22.00,4250,1700,0,'2024-01-01'),
            (1,2, 55000, 8000,4800,1600,0, 20.00,2750,1100,0,'2024-01-01'),
            (1,3, 72000,10000,5400,2000,0, 21.00,3600,1440,0,'2024-01-01'),
            (1,4, 90000,13000,7200,2600,0, 23.00,4500,1800,0,'2024-01-01'),
            (1,5, 60000, 9000,5000,1800,0, 20.00,3000,1200,0,'2024-01-01'),
            (1,6, 78000,11000,6000,2200,0, 21.00,3900,1560,0,'2024-01-01'),
            (1,7, 82000,12000,6000,2400,0, 22.00,4100,1640,0,'2024-01-01'),
            (1,8, 58000, 8500,4800,1700,0, 20.00,2900,1160,0,'2024-01-01'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO compensation
              (company_id,employee_id,basic_salary,housing_allowance,transport_allowance,
               meal_allowance,other_allowances,income_tax_rate,social_insurance,
               health_insurance,other_deductions,effective_date)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, comp)

        # 6 — Leave balances
        yr = date.today().year
        for eid in range(1, 9):
            cur.execute("""
                INSERT IGNORE INTO leave_balances
                  (company_id,employee_id,year,annual_total,annual_used,sick_total,sick_used)
                VALUES(%s,%s,%s,21,%s,14,%s)
            """, (1, eid, yr, random.randint(0,10), random.randint(0,5)))

        conn.commit()
        print("✅  Database seeded!\n")
        print("  ┌───────────────┬────────────────┬─────────────┐")
        print("  │ Role          │ Username       │ Password    │")
        print("  ├───────────────┼────────────────┼─────────────┤")
        print("  │ Admin         │ admin          │ Admin@123   │")
        print("  │ HR Manager    │ hr_manager     │ HR@123456   │")
        print("  │ CHRO          │ chro           │ CHRO@1234   │")
        print("  └───────────────┴────────────────┴─────────────┘")

    except Exception as exc:
        conn.rollback()
        print(f"❌  Seed failed: {exc}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run()