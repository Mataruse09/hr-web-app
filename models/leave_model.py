from models.db import query, mutate
from datetime import datetime


def get_requests(company_id: int, status_filter: str = None):
    base = """
        SELECT lr.*, e.first_name, e.last_name, e.employee_code,
               d.name AS dept_name, u.full_name AS reviewer_name
        FROM   leave_requests lr
        JOIN   employees_core  e ON e.id  = lr.employee_id
        LEFT JOIN departments  d ON d.id  = e.department_id
        LEFT JOIN users        u ON u.id  = lr.reviewed_by
        WHERE  lr.company_id=%s
    """
    params = [company_id]
    if status_filter and status_filter != 'All':
        base += " AND lr.status=%s"
        params.append(status_filter)
    base += " ORDER BY lr.created_at DESC"
    return query(base, tuple(params))


def get_by_employee(employee_id: int, company_id: int):
    return query("""
        SELECT * FROM leave_requests
        WHERE employee_id=%s AND company_id=%s
        ORDER BY created_at DESC
    """, (employee_id, company_id))


def create(company_id: int, data: dict) -> int:
    return mutate("""
        INSERT INTO leave_requests
          (company_id,employee_id,leave_type,start_date,end_date,
           days_requested,reason,status)
        VALUES(%s,%s,%s,%s,%s,%s,%s,'Pending')
    """, (
        company_id,
        data['employee_id'], data['leave_type'],
        data['start_date'],  data['end_date'],
        data['days_requested'], data.get('reason', ''),
    ))


def update_status(request_id: int, company_id: int,
                  status: str, reviewed_by: int, notes: str = ''):
    mutate("""
        UPDATE leave_requests
        SET status=%s, reviewed_by=%s, reviewed_at=%s, review_notes=%s
        WHERE id=%s AND company_id=%s
    """, (status, reviewed_by, datetime.utcnow(), notes, request_id, company_id))

    # Update leave balance if approved
    if status == 'Approved':
        row = query(
            "SELECT * FROM leave_requests WHERE id=%s", (request_id,), one=True
        )
        if row and row['leave_type'] in ('Annual', 'Sick', 'Emergency'):
            col_map = {
                'Annual':    'annual_used',
                'Sick':      'sick_used',
                'Emergency': 'emergency_used',
            }
            col = col_map[row['leave_type']]
            yr  = row['start_date'].year
            mutate(f"""
                INSERT INTO leave_balances
                  (company_id, employee_id, year)
                VALUES(%s,%s,%s)
                ON DUPLICATE KEY UPDATE {col} = {col} + %s
            """, (row['company_id'], row['employee_id'], yr, row['days_requested']))


def get_balance(employee_id: int, company_id: int, year: int):
    return query("""
        SELECT * FROM leave_balances
        WHERE employee_id=%s AND company_id=%s AND year=%s
    """, (employee_id, company_id, year), one=True)


def on_leave_today(company_id: int, today: str) -> int:
    row = query("""
        SELECT COUNT(DISTINCT employee_id) AS cnt
        FROM   leave_requests
        WHERE  company_id=%s AND status='Approved'
          AND  %s BETWEEN start_date AND end_date
    """, (company_id, today), one=True)
    return row['cnt'] if row else 0