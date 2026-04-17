from datetime import date
from models.db import query, mutate


# ── Read ────────────────────────────────────────────────────────────────────

def get_all(company_id: int):
    return query("""
        SELECT e.*, d.name AS department_name
        FROM   employees_core e
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE  e.company_id = %s
        ORDER BY e.first_name, e.last_name
    """, (company_id,))


def get_by_id(emp_id: int, company_id: int):
    return query("""
        SELECT e.*, d.name AS department_name
        FROM   employees_core e
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE  e.id = %s AND e.company_id = %s
    """, (emp_id, company_id), one=True)


def get_by_user_id(user_id: int, company_id: int):
    return query(
        "SELECT * FROM employees_core WHERE user_id = %s AND company_id = %s",
        (user_id, company_id),
        one=True
    )


def get_active_count(company_id: int) -> int:
    row = query(
        "SELECT COUNT(*) AS cnt FROM employees_core "
        "WHERE company_id=%s AND status='Active'",
        (company_id,), one=True
    )
    return row['cnt'] if row else 0


def get_terminated_count(company_id: int) -> int:
    row = query(
        "SELECT COUNT(*) AS cnt FROM employees_core "
        "WHERE company_id=%s AND status='Terminated'",
        (company_id,), one=True
    )
    return row['cnt'] if row else 0


def get_total_count(company_id: int) -> int:
    row = query(
        "SELECT COUNT(*) AS cnt FROM employees_core WHERE company_id=%s",
        (company_id,), one=True
    )
    return row['cnt'] if row else 0


def search(company_id: int, term: str):
    t = f"%{term}%"
    return query("""
        SELECT e.*, d.name AS department_name
        FROM   employees_core e
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE  e.company_id = %s
          AND (e.first_name ILIKE %s OR e.last_name ILIKE %s
               OR e.email ILIKE %s OR e.employee_code ILIKE %s)
        ORDER BY e.first_name
    """, (company_id, t, t, t, t))


# ── Write ───────────────────────────────────────────────────────────────────

def create(company_id: int, data: dict) -> int:
    return mutate("""
        INSERT INTO employees_core
          (company_id,employee_code,first_name,last_name,email,phone,
           department_id,job_title,employment_type,status,hire_date)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        company_id,
        data.get('employee_code'),
        data.get('first_name'),
        data.get('last_name'),
        data.get('email'),
        data.get('phone',''),
        data.get('department_id') or None,
        data.get('job_title',''),
        data.get('employment_type','Full-Time'),
        data.get('status','Active'),
        data.get('hire_date'),
    ))


def link_user(emp_id: int, user_id: int, company_id: int):
    return mutate(
        "UPDATE employees_core SET user_id=%s WHERE id=%s AND company_id=%s",
        (user_id, emp_id, company_id)
    )


def update(emp_id: int, company_id: int, data: dict):
    mutate("""
        UPDATE employees_core SET
          first_name=%s, last_name=%s, email=%s, phone=%s,
          department_id=%s, job_title=%s, employment_type=%s,
          status=%s, hire_date=%s
        WHERE id=%s AND company_id=%s
    """, (
        data.get('first_name'),
        data.get('last_name'),
        data.get('email'),
        data.get('phone',''),
        data.get('department_id') or None,
        data.get('job_title',''),
        data.get('employment_type','Full-Time'),
        data.get('status','Active'),
        data.get('hire_date'),
        emp_id, company_id,
    ))


def delete(emp_id: int, company_id: int):
    mutate(
        "DELETE FROM employees_core WHERE id=%s AND company_id=%s",
        (emp_id, company_id)
    )


# ── Departments ─────────────────────────────────────────────────────────────

def get_departments(company_id: int):
    return query(
        "SELECT * FROM departments WHERE company_id=%s ORDER BY name",
        (company_id,)
    )


def create_department(company_id: int, name: str, description: str = '') -> int:
    return mutate(
        "INSERT INTO departments (company_id,name,description) VALUES(%s,%s,%s)",
        (company_id, name, description)
    )


def get_next_employee_code(company_id: int) -> str:
    row = query("""
        SELECT employee_code
        FROM employees_core
        WHERE company_id = %s
        ORDER BY id DESC
        LIMIT 1
    """, (company_id,), one=True)

    if not row or not row.get('employee_code'):
        return "EMP0001"

    try:
        last_code = row['employee_code']
        number = int(last_code.replace('EMP', ''))
        return f"EMP{number + 1:04d}"
    except Exception:
        return "EMP0001"


def get_average_rating(company_id: int, employee_id: int) -> float:
    row = query(
        "SELECT AVG(overall_rating) AS avg_rating "
        "FROM performance_reviews "
        "WHERE company_id=%s AND employee_id=%s AND status IN ('Submitted','Acknowledged')",
        (company_id, employee_id), one=True
    )
    return round(float(row['avg_rating'] or 0), 1) if row else 0.0


def add_performance_review(company_id: int, employee_id: int, reviewer_id: int, rating: float, comments: str):
    return mutate(
        "INSERT INTO performance_reviews (company_id, employee_id, reviewer_id, review_period, review_date, overall_rating, comments, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (company_id, employee_id, reviewer_id, 'Auto-'+str(date.today().year), date.today(), rating, comments, 'Submitted')
    )