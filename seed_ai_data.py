"""
Enhanced Database seeder — adds data for AI Analytics features.
Run this AFTER running the original seed_db.py to populate AI-related data.

Usage:
  python seed_ai_data.py
"""
import mysql.connector
from mysql.connector import Error
from datetime import date, datetime, timedelta
import random

# Import DB config from seed_db to ensure same connection
import seed_db

DB = seed_db.DB


def run():
    conn = None
    cur = None
    try:
        # Connect - use DB from seed_db (same connection)
        conn = mysql.connector.connect(**DB)

        cur = conn.cursor()
        company_id = 1

        # Get existing employees - use same query as seed_db.py
        cur.execute("SELECT id, department_id, job_title FROM employees_core WHERE company_id = %s", (company_id,))
        employees = cur.fetchall()
        
        if not employees:
            print("❌ No employees found. Run seed_db.py first!")
            return

        print(f"Found {len(employees)} employees, adding AI analytics data...")

        # ═══════════════════════════════════════════════════════════════════
        # 1. ADD MORE EMPLOYEES (for meaningful AI analysis)
        # ═══════════════════════════════════════════════════════════════════
        
        # Check if we already have enough employees
        if len(employees) < 10:
            new_employees = [
                (company_id, 'EMP003', 'Alice', 'Williams', 'alice@tech.com', '555-0103', 1, 'HR Manager', 'Full-Time', 'Active', '2021-06-15'),
                (company_id, 'EMP004', 'Bob', 'Anderson', 'bob@tech.com', '555-0104', 2, 'Senior Developer', 'Full-Time', 'Active', '2020-03-20'),
                (company_id, 'EMP005', 'Carol', 'Taylor', 'carol@tech.com', '555-0105', 3, 'Financial Analyst', 'Full-Time', 'Active', '2022-09-10'),
                (company_id, 'EMP006', 'David', 'Brown', 'david@tech.com', '555-0106', 4, 'Sales Executive', 'Full-Time', 'Active', '2023-02-01'),
                (company_id, 'EMP007', 'Eva', 'Martinez', 'eva@tech.com', '555-0107', 5, 'Operations Manager', 'Full-Time', 'Active', '2019-11-15'),
                (company_id, 'EMP008', 'Frank', 'Garcia', 'frank@tech.com', '555-0108', 2, 'Junior Developer', 'Full-Time', 'Active', '2024-01-15'),
                (company_id, 'EMP009', 'Grace', 'Lee', 'grace@tech.com', '555-0109', 1, 'Recruiter', 'Full-Time', 'Active', '2023-07-01'),
                (company_id, 'EMP010', 'Henry', 'Wilson', 'henry@tech.com', '555-0110', 3, 'Accountant', 'Full-Time', 'Active', '2021-03-01'),
            ]
            cur.executemany("""
                INSERT IGNORE INTO employees_core
                  (company_id, employee_code, first_name, last_name, email, phone,
                   department_id, job_title, employment_type, status, hire_date)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, new_employees)
            conn.commit()
            
            # Refresh employee list
            cur.execute("SELECT id, department_id, job_title FROM employees_core WHERE company_id = %s", (company_id,))
            employees = cur.fetchall()
            print(f"✅ Added employees, total now: {len(employees)}")

        # ═══════════════════════════════════════════════════════════════════
        # 2. ATTENDANCE RECORDS (past 90 days for each employee)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📅 Adding attendance records...")
        
        # Check existing attendance
        cur.execute("SELECT COUNT(*) as cnt FROM attendance WHERE company_id = %s", (company_id,))
        existing_attendance = cur.fetchone()[0]
        
        if existing_attendance < 100:
            attendance_records = []
            today = date.today()
            
            for emp in employees:
                emp_id = emp[0]
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
                        check_in = f"{9:{random.randint(0, 2)}}:{random.randint(10, 59):02d}:00"
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
            
            print(f"✅ Added attendance records")
        
        # ═══════════════════════════════════════════════════════════════════
        # 3. LEAVE BALANCES
        # ═══════════════════════════════════════════════════════════════════
        
        print("🏖️ Adding leave balances...")
        current_year = date.today().year
        
        for emp in employees:
            emp_id = emp[0]
            annual_total = random.choice([18, 20, 21, 22, 25])
            annual_used = random.randint(0, min(15, annual_total - 1))
            
            cur.execute("""
                INSERT IGNORE INTO leave_balances 
                  (company_id, employee_id, year, annual_total, annual_used)
                VALUES(%s, %s, %s, %s, %s)
            """, (company_id, emp_id, current_year, annual_total, annual_used))
        
        conn.commit()
        print(f"✅ Added leave balances for {len(employees)} employees")

        # ═══════════════════════════════════════════════════════════════════
        # 4. LEAVE REQUESTS (some pending, some approved)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📋 Adding leave requests...")
        
        leave_types = ['Annual Leave', 'Sick Leave', 'Personal Leave', 'Maternity Leave', 'Paternity Leave']
        statuses = ['Approved', 'Approved', 'Approved', 'Pending', 'Rejected']
        
        for emp in employees[:8]:  # Only first 8 employees
            emp_id = emp[0]
            # Add 1-3 leave requests per employee
            for _ in range(random.randint(1, 3)):
                start_offset = random.randint(5, 60)
                start_date = date.today() - timedelta(days=start_offset)
                days = random.randint(1, 5)
                end_date = start_date + timedelta(days=days)
                
                cur.execute("""
                    INSERT IGNORE INTO leave_requests 
                      (company_id, employee_id, leave_type, start_date, end_date, 
                       days_requested, reason, status, reviewed_by, reviewed_at, review_notes)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    company_id, emp_id, 
                    random.choice(leave_types),
                    start_date, end_date, days,
                    'Personal reason',
                    random.choice(statuses),
                    1, datetime.now(), 'Approved'
                ))
        
        conn.commit()
        print(f"✅ Added leave requests")

        # ═══════════════════════════════════════════════════════════════════
        # 5. COMPENSATION (salary data for each employee)
        # ═══════════════════════════════════════════════════════════════════
        
        print("💰 Adding compensation data...")
        
        # Base salaries by job title (in USD)
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
        
        for emp in employees:
            emp_id = emp[0]
            job_title = emp[2] if len(emp) > 2 else 'Developer'
            
            # Get salary range or use default
            salary_range = salary_ranges.get(job_title, (50000, 80000))
            basic_salary = random.randint(salary_range[0], salary_range[1])
            
            cur.execute("""
                INSERT IGNORE INTO compensation 
                  (company_id, employee_id, basic_salary, currency)
                VALUES(%s, %s, %s, 'USD')
            """, (company_id, emp_id, basic_salary))
        
        conn.commit()
        print(f"✅ Added compensation data for {len(employees)} employees")

        # ═══════════════════════════════════════════════════════════════════
        # 6. PAYROLL RUNS (with overtime for some employees)
        # ═══════════════════════════════════════════════════════════════════
        
        print("💵 Adding payroll data...")
        
        # Generate last 6 months of payroll data
        for month_offset in range(6):
            pay_date = date.today() - timedelta(days=30 * month_offset)
            pay_period = pay_date.strftime('%Y-%m')
            
            for emp in employees:
                emp_id = emp[0]
                
                # Get basic salary
                cur.execute("""
                    SELECT basic_salary FROM compensation 
                    WHERE employee_id = %s AND company_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (emp_id, company_id))
                comp_result = cur.fetchone()
                basic_salary = comp_result[0] if comp_result else 60000
                
                # Calculate monthly salary
                monthly_salary = basic_salary / 12
                
                # Add overtime for some employees (30% chance)
                overtime_hours = round(random.uniform(0, 20), 1) if random.random() < 0.3 else 0
                overtime_amount = overtime_hours * 25  # $25/hour
                
                # Allowances
                housing = random.choice([0, 500, 800, 1000])
                transport = random.choice([0, 200, 300, 400])
                meal = random.choice([0, 150, 200])
                
                # Bonus (occasional)
                bonus = random.choice([0, 0, 0, 500, 1000, 2000])
                
                # Deductions (simplified)
                gross = monthly_salary + overtime_amount + housing + transport + meal + bonus
                tax = round(gross * 0.15, 2)  # 15% tax
                social = round(gross * 0.05, 2)  # 5% social security
                health = round(gross * 0.03, 2)  # 3% health
                net = gross - tax - social - health
                
                cur.execute("""
                    INSERT IGNORE INTO payroll_runs 
                      (company_id, employee_id, pay_period, basic_salary, gross_salary,
                       overtime_hours, overtime_amount, housing_allowance, transport_allowance,
                       meal_allowance, performance_bonus, income_tax, social_security, 
                       health_insurance, net_salary, status)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Approved')
                """, (
                    company_id, emp_id, pay_period, 
                    round(monthly_salary, 2), round(gross, 2),
                    overtime_hours, round(overtime_amount, 2),
                    housing, transport, meal, round(bonus, 2),
                    tax, social, health, round(net, 2)
                ))
        
        conn.commit()
        print(f"✅ Added payroll data (6 months)")

        # ═══════════════════════════════════════════════════════════════════
        # 7. APPRAISALS (performance reviews)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📊 Adding appraisal data...")
        
        review_periods = ['Q1 2025', 'Q4 2024', 'Q3 2024', 'Annual 2024']
        
        for emp in employees[:8]:  # Only first 8 employees
            emp_id = emp[0]
            # Add 1-2 appraisals per employee
            for _ in range(random.randint(1, 2)):
                review_date = date.today() - timedelta(days=random.randint(30, 180))
                rating = random.choice([2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
                
                cur.execute("""
                    INSERT IGNORE INTO appraisals 
                      (company_id, employee_id, reviewer_id, review_period, review_date, 
                       overall_rating, status)
                    VALUES(%s, %s, %s, %s, %s, %s, 'Completed')
                """, (
                    company_id, emp_id, 1,
                    random.choice(review_periods),
                    review_date, rating
                ))
        
        conn.commit()
        print(f"✅ Added appraisal data")

        # ═══════════════════════════════════════════════════════════════════
        # 8. ATTRITION RECORDS (for historical analysis)
        # ═══════════════════════════════════════════════════════════════════
        
        print("📉 Adding attrition records...")
        
        # Add some past attrition data
        past_employees = [
            (company_id, 'EMP101', 'Former', 'Employee1', 'former1@tech.com', '555-0201', 2, 'Developer', '2022-01-15', '2024-06-30', 'Resignation'),
            (company_id, 'EMP102', 'Former', 'Employee2', 'former2@tech.com', '555-0202', 3, 'Analyst', '2021-05-20', '2024-03-15', 'Better Opportunity'),
            (company_id, 'EMP103', 'Former', 'Employee3', 'former3@tech.com', '555-0203', 4, 'Sales', '2023-02-10', '2024-08-20', 'Retirement'),
        ]
        
        cur.executemany("""
            INSERT IGNORE INTO attrition_records 
              (company_id, employee_id, first_name, last_name, email, phone,
               department_id, job_title, hire_date, termination_date, termination_reason)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, past_employees)
        
        conn.commit()
        print(f"✅ Added attrition records")

        print("\n" + "="*60)
        print("🎉 AI Analytics data seeding completed!")
        print("="*60)
        print("\nThe following data has been added:")
        print(f"  • {len(employees)} employees")
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