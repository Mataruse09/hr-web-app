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
          AND (e.first_name LIKE %s OR e.last_name LIKE %s
               OR e.email LIKE %s OR e.employee_code LIKE %s)
        ORDER BY e.first_name
    """, (company_id, t, t, t, t))


# ── Write ───────────────────────────────────────────────────────────────────

def create(company_id: int, data: dict) -> int:
    return mutate("""
        INSERT INTO employees_core
          (company_id,employee_code,first_name,last_name,email,phone,
           department_id,job_title,employment_type,status,hire_date,
           date_of_birth,gender,nationality,address,
           emergency_contact_name,emergency_contact_phone)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        company_id,
        data['employee_code'], data['first_name'], data['last_name'],
        data['email'],         data.get('phone',''),
        data.get('department_id') or None,
        data.get('job_title',''),  data.get('employment_type','Full-Time'),
        data.get('status','Active'), data['hire_date'],
        data.get('date_of_birth') or None,
        data.get('gender','Prefer not to say'),
        data.get('nationality',''), data.get('address',''),
        data.get('emergency_contact_name',''),
        data.get('emergency_contact_phone',''),
    ))


def update(emp_id: int, company_id: int, data: dict):
    mutate("""
        UPDATE employees_core SET
          first_name=%s, last_name=%s, email=%s, phone=%s,
          department_id=%s, job_title=%s, employment_type=%s,
          status=%s, hire_date=%s, date_of_birth=%s, gender=%s,
          nationality=%s, address=%s,
          emergency_contact_name=%s, emergency_contact_phone=%s,
          termination_date=%s
        WHERE id=%s AND company_id=%s
    """, (
        data['first_name'], data['last_name'], data['email'],
        data.get('phone',''),
        data.get('department_id') or None,
        data.get('job_title',''),  data.get('employment_type','Full-Time'),
        data.get('status','Active'), data['hire_date'],
        data.get('date_of_birth') or None,
        data.get('gender','Prefer not to say'),
        data.get('nationality',''), data.get('address',''),
        data.get('emergency_contact_name',''),
        data.get('emergency_contact_phone',''),
        data.get('termination_date') or None,
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
    row = query(
        "SELECT COUNT(*) AS cnt FROM employees_core WHERE company_id=%s",
        (company_id,), one=True
    )
    n = (row['cnt'] if row else 0) + 1
    return f"EMP{n:04d}"