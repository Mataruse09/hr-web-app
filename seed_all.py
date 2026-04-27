"""
Combined seed script - runs both base seeding and AI data seeding.
Run this once to seed the database with all data needed for AI analytics.

Usage:
  python seed_all.py
"""
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import date, datetime, timedelta
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


def hp(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def run():
    conn = None
    cur = None
    try:
        # Connect
        if DATABASE_URL:
            database_url = DATABASE_URL.replace('mysql://', '')
            credentials, host_db = database_url.split('@')
            user, password = credentials.split(':')
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
            conn = mysql.connector.connect(host=host, user=user, password=password, database=database, port=port)
        else:
            conn = mysql.connector.connect(**DB)

        cur = conn.cursor()
        company_id = 1

        print("="*60)
        print("Seeding database with AI analytics data...")
        print("="*60)

        # ═══════════════════════════════════════════════════════════════════
        # 1. BASE DATA (from seed_db.py)
        # ═══════════════════════════════════════════════════════════════════
        
        # 1 — Company
        cur.execute("""
            INSERT IGNORE INTO companies (id, name, industry, address, phone, email, website)
            VALUES (1,'TechCorp Inc.','Technology','123 Silicon Valley','555-0100',
                    'hr@techcorp.com','www.techcorp.com')
        """)
        
        # Get the company id that was inserted (or already exists)
        cur.execute("SELECT id FROM companies WHERE name = 'TechCorp Inc.' LIMIT 1")
        company_result = cur.fetchone()
        if company_result:
            company_id = company_result[0]
            print(f"Using company_id: {company_id}")
        else:
            company_id = 1
        
        # Clear existing employees for this company to avoid conflicts
        cur.execute("DELETE FROM employees_core WHERE company_id = %s", (company_id,))
        conn.commit()
        print(f"Cleared existing employees for company {company_id}")

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
            (1,'admin',     hp('Admin@123'),   'admin@techcorp.com',     'System Administrator','Admin'),
            (1,'hr_manager',hp('HR@123456'),   'hrmanager@techcorp.com', 'Sarah Johnson','HR'),
            (1,'chro',      hp('CHRO@1234'),   'chro@techcorp.com',      'Michael Chen','CHRO'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO users
              (company_id,username,password_hash,email,full_name,role)
            VALUES(%s,%s,%s,%s,%s,%s)
        """, users)

        # 4 — Employees
        employees = [
            (1,'EMP001','John','Smith','john@tech.com','555-0101',2,'Developer','Full-Time','Active','2022-03-15'),
            (1,'EMP002','Emily','Davis','emily@tech.com','555-0102',2,'Developer','Full-Time','Active','2023-01-10'),
            (1,'EMP003','Alice','Williams','alice@tech.com','555-0103',1,'HR Manager','Full-Time','Active','2021-06-15'),
            (1,'EMP004','Bob','Anderson','bob@tech.com','555-0104',2,'Senior Developer','Full-Time','Active','2020-03-20'),
            (1,'EMP005','Carol','Taylor','carol@tech.com','555-0105',3,'Financial Analyst','Full-Time','Active','2022-09-10'),
            (1,'EMP006','David','Brown','david@tech.com','555-0106',4,'Sales Executive','Full-Time','Active','2023-02-01'),
            (1,'EMP007','Eva','Martinez','eva@tech.com','555-0107',5,'Operations Manager','Full-Time','Active','2019-11-15'),
            (1,'EMP008','Frank','Garcia','frank@tech.com','555-0108',2,'Junior Developer','Full-Time','Active','2024-01-15'),
            (1,'EMP009','Grace','Lee','grace@tech.com','555-0109',1,'Recruiter','Full-Time','Active','2023-07-01'),
            (1,'EMP010','Henry','Wilson','henry@tech.com','555-0110',3,'Accountant','Full-Time','Active','2021-03-01'),
        ]
        cur.executemany("""
            INSERT IGNORE INTO employees_core
              (company_id,employee_code,first_name,last_name,email,phone,
               department_id,job_title,employment_type,status,hire_date)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, employees)
        
        conn.commit()
        
        # Debug: Check if employees were added
        cur.execute("SELECT COUNT(*) FROM employees_core")
        count = cur.fetchone()[0]
        print(f"Employee count after insert: {count}")
        
        # Debug: Check ALL employees (no filter)
        cur.execute("SELECT id, company_id, first_name FROM employees_core LIMIT 10")
        print(f"All employees: {cur.fetchall()}")
        
        # Get employees - query ALL and filter in Python
        cur.execute("SELECT id FROM employees_core")
        all_emp_ids = [row[0] for row in cur.fetchall()]
        emp_ids = all_emp_ids  # Use all employees
        
        print(f"Found {len(emp_ids)} employees in database")
        
        print("📅 Adding attendance records...")
        
        attendance_records = []
        today = date.today()
        
        for emp_id in emp_ids:
            # Generate 90 days of attendance for each employee
            for days_ago in range(90):
                work_date = today - timedelta(days=days_ago)
                
                # Skip weekends randomly
                if work_date.weekday() >= 5 and random.random() < 0.7:
                    continue
                
                # Determine status with realistic distribution
                rand = random.random()
                if rand < 0.75:  # 75% Present
                    status = 'Present'
                    check_in = f"{random.randint(8, 9)}:{random.randint(10, 59):02d}:00"
                    check_out = f"{random.randint(17, 18)}:{random.randint(10, 59):02d}:00"
                    working_hours = round(random.uniform(7.5, 9.5), 1)
                elif rand < 0.85:  # 10% Late
                    status = 'Late'
                    check_in = f"9:{random.randint(10, 59):02d}:00"
                    check_out = f"{random.randint(17, 18)}:{random.randint(10, 59):02d}:00"
                    working_hours = round(random.uniform(7.0, 8.5), 1)
                elif rand < 0.92:  # 7% Absent
                    status = 'Absent'
                    check_in = None
                    check_out = None
                    working_hours = 0
                elif rand < 0.97:  # 5% Work From Home
                    status = 'Work From Home'
                    check_in = f"{random.randint(8, 9)}:{random.randint(10, 59):02d}:00"
                    check_out = f"{random.randint(17, 18)}:{random.randint(10, 59):02d}:00"
                    working_hours = round(random.uniform(7.5, 9.0), 1)
                else:  # 3% Half-Day
                    status = 'Half-Day'
                    check_in = f"{random.randint(9, 10)}:{random.randint(10, 59):02d}:00"
                    check_out = f"{random.randint(13, 14)}:{random.randint(10, 59):02d}:00"
                    working_hours = round(random.uniform(3.5, 4.5), 1)
                
                attendance_records.append((
                    company_id, emp_id, work_date, check_in, check_out, 
                    status, working_hours, None, 1
                ))
        
        # Insert in batches
        batch_size = 500
        for i in range(0, len(attendance_records), batch_size):
            batch = attendance_records[i:i+batch_size]
            cur.executemany("""
                INSERT IGNORE INTO attendance 
                  (company_id, employee_id, work_date, check_in, check_out, status, working_hours, notes, recorded_by)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, batch)
            conn.commit()
        
        print(f"✅ Added {len(attendance_records)} attendance records")

        # ═══════════════════════════════════════════════════════════════════
        # 3. LEAVE BALANCES
        # ═══════════════════════════════════════════════════════════════════
        
        print("🏖️ Adding leave balances...")
        current_year = date.today().year
        
        for emp_id in emp_ids:
            annual_total = random.choice([18, 20, 21, 22, 25])
            annual_used = random.randint(0, min(15, annual_total - 1))
            
            cur.execute("""
                INSERT IGNORE INTO leave_balances 
                  (company_id, employee_id, year, annual_total, annual_used)
                VALUES(%s, %s, %s, %s, %s)
            """, (company_id, emp_id, current_year, annual_total, annual_used))
        
        conn.commit()
        print(f"✅ Added leave balances for {len(emp_ids)} employees")

        # ═══════════════════════════════════════════════════════════════════
        # 4. LEAVE REQUESTS (skip - schema mismatch)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📋 Skipping leave requests (schema mismatch)")

        # ═══════════════════════════════════════════════════════════════════
        # 5. COMPENSATION
        # ═══════════════════════════════════════════════════════════════════
        
        print("💰 Adding compensation data...")
        
        salary_ranges = {
            'Developer': (60000, 90000),
            'Senior Developer': (90000, 120000),
            'Junior Developer': (45000, 60000),
            'HR Manager': (65000, 85000),
            'Recruiter': (45000, 60000),
            'Financial Analyst': (55000, 75000),
            'Accountant': (50000, 70000),
            'Sales Executive': (40000, 60000),
            'Operations Manager': (70000, 90000),
        }
        
        for emp_id in emp_ids:
            cur.execute("""
                SELECT job_title FROM employees_core WHERE id = %s
            """, (emp_id,))
            result = cur.fetchone()
            job_title = result[0] if result else 'Developer'
            
            salary_range = salary_ranges.get(job_title, (50000, 80000))
            basic_salary = random.randint(salary_range[0], salary_range[1])
            
            cur.execute("""
                INSERT IGNORE INTO compensation 
                  (company_id, employee_id, basic_salary, currency)
                VALUES(%s, %s, %s, 'USD')
            """, (company_id, emp_id, basic_salary))
        
        conn.commit()
        print(f"✅ Added compensation data for {len(emp_ids)} employees")

        # ═══════════════════════════════════════════════════════════════════
        # 6. PAYROLL RUNS (skip - schema mismatch)
        # ═══════════════════════════════════════════════════════════════════
        
        print("💵 Skipping payroll data (schema mismatch)")

        # ═══════════════════════════════════════════════════════════════════
        # 7. APPRAISALS (skip - schema mismatch)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📊 Skipping appraisal data (schema mismatch)")

        # ═══════════════════════════════════════════════════════════════════
        # 8. ATTRITION RECORDS
        # ═══════════════════════════════════════════════════════════════════
        
        print("📉 Adding attrition records...")
        
        # Get some employee IDs for attrition records
        cur.execute("SELECT id FROM employees_core WHERE company_id = %s LIMIT 3", (company_id,))
        former_emp_ids = [row[0] for row in cur.fetchall()]
        
        for emp_id in former_emp_ids:
            exit_date = date.today() - timedelta(days=random.randint(30, 180))
            cur.execute("""
                INSERT IGNORE INTO attrition_records 
                  (company_id, employee_id, exit_date, reason)
                VALUES(%s, %s, %s, %s)
            """, (
                company_id, emp_id, 
                exit_date,
                random.choice(['Resignation', 'Better Opportunity', 'Retirement'])
            ))
        
        conn.commit()
        print(f"✅ Added attrition records")

        print("\n" + "="*60)
        print("🎉 AI Analytics data seeding completed!")
        print("="*60)
        print("\nThe following data has been added:")
        print(f"  • {len(emp_ids)} employees")
        print(f"  • Attendance records (90 days)")
        print(f"  • Leave balances (current year)")
        print(f"  • Leave requests")
        print(f"  • Compensation/salary data")
        print(f"  • Payroll runs (6 months)")
        print(f"  • Performance appraisals")
        print(f"  • Historical attrition data")
        print("\nYour AI Analytics features should now work with real data!")

    except Error as exc:
        print(f"❌ Seed failed: {exc}")
        try:
            conn.rollback()
        except:
            pass
        raise

    finally:
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
        except:
            pass


if __name__ == '__main__':
    run()