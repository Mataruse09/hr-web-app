from models.db import query, mutate
from datetime import date


def get_by_date(company_id: int, work_date: str):
    return query("""
        SELECT a.*, e.first_name, e.last_name, e.employee_code, d.name AS dept
        FROM   attendance a
        JOIN   employees_core e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE  a.company_id=%s AND a.work_date=%s
        ORDER BY e.first_name
    """, (company_id, work_date))


def get_logs(company_id: int, from_date: str, to_date: str, emp_id=None):
    if emp_id:
        return query("""
            SELECT a.*, e.first_name, e.last_name, e.employee_code
            FROM   attendance a
            JOIN   employees_core e ON e.id = a.employee_id
            WHERE  a.company_id=%s AND a.work_date BETWEEN %s AND %s
              AND  a.employee_id=%s
            ORDER BY a.work_date DESC, e.first_name
        """, (company_id, from_date, to_date, emp_id))
    return query("""
        SELECT a.*, e.first_name, e.last_name, e.employee_code,
               d.name AS dept
        FROM   attendance a
        JOIN   employees_core e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE  a.company_id=%s AND a.work_date BETWEEN %s AND %s
        ORDER BY a.work_date DESC, e.first_name
    """, (company_id, from_date, to_date))


def upsert(company_id: int, employee_id: int, work_date: str,
           check_in, check_out, status: str, notes: str, recorded_by: int):
    """Insert or update an attendance record for a given employee+date."""
    hours = None
    if check_in and check_out:
        from datetime import datetime
        fmt = "%H:%M"
        try:
            ci = datetime.strptime(str(check_in)[:5], fmt)
            co = datetime.strptime(str(check_out)[:5], fmt)
            diff = (co - ci).seconds / 3600
            hours = round(diff, 2) if diff > 0 else None
        except ValueError:
            hours = None

    mutate("""
        INSERT INTO attendance
          (company_id,employee_id,work_date,check_in,check_out,status,
           working_hours,notes,recorded_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          check_in=%s, check_out=%s, status=%s,
          working_hours=%s, notes=%s, recorded_by=%s
    """, (
        company_id, employee_id, work_date,
        check_in or None, check_out or None, status,
        hours, notes, recorded_by,
        # UPDATE part
        check_in or None, check_out or None, status,
        hours, notes, recorded_by,
    ))


def today_summary(company_id: int, today: str):
    row = query("""
        SELECT
          SUM(status IN ('Present','Late','Work From Home','Half-Day')) AS present,
          SUM(status = 'Absent') AS absent,
          COUNT(*) AS total
        FROM attendance
        WHERE company_id=%s AND work_date=%s
    """, (company_id, today), one=True)
    return row or {'present': 0, 'absent': 0, 'total': 0}


def monthly_present_days(company_id: int, employee_id: int,
                         year: int, month: int) -> int:
    row = query("""
        SELECT COUNT(*) AS cnt FROM attendance
        WHERE company_id=%s AND employee_id=%s
          AND YEAR(work_date)=%s AND MONTH(work_date)=%s
          AND status IN ('Present','Late','Work From Home','Half-Day')
    """, (company_id, employee_id, year, month), one=True)
    return row['cnt'] if row else 0