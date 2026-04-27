from models.db import query, mutate
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


def get_requests(company_id: int, status_filter: str = None):
    try:
        # Note: Calculate days_requested from start and end dates
        base = """
            SELECT lr.id, lr.company_id, lr.employee_id, lr.leave_type, 
                   lr.start_date, lr.end_date, 
                   DATEDIFF(lr.end_date, lr.start_date) + 1 AS days_requested,
                   lr.status, lr.created_at,
                   e.first_name, e.last_name, e.employee_code,
                   d.name AS dept_name
            FROM   leave_requests lr
            JOIN   employees_core  e ON e.id  = lr.employee_id
            LEFT JOIN departments  d ON d.id  = e.department_id
            WHERE  lr.company_id=%s
        """
        params = [company_id]
        if status_filter and status_filter != 'All':
            base += " AND lr.status=%s"
            params.append(status_filter)
        base += " ORDER BY lr.created_at DESC"
        return query(base, tuple(params))
    except Exception as e:
        logger.error(f"Error getting leave requests for company {company_id}: {e}")
        return []


def get_by_employee(employee_id: int, company_id: int):
    try:
        return query("""
            SELECT * FROM leave_requests
            WHERE employee_id=%s AND company_id=%s
            ORDER BY created_at DESC
        """, (employee_id, company_id))
    except Exception as e:
        logger.error(f"Error getting leave requests for employee {employee_id}: {e}")
        return []


def create(company_id: int, data: dict) -> int:
    """Create a new leave request - days_requested will be calculated from dates."""
    from datetime import datetime as dt
    
    start_date = dt.strptime(data['start_date'], '%Y-%m-%d').date() if isinstance(data['start_date'], str) else data['start_date']
    end_date = dt.strptime(data['end_date'], '%Y-%m-%d').date() if isinstance(data['end_date'], str) else data['end_date']
    
    return mutate("""
        INSERT INTO leave_requests
          (company_id, employee_id, leave_type, start_date, end_date, status)
        VALUES(%s, %s, %s, %s, %s, 'Pending')
    """, (
        company_id,
        data['employee_id'], data['leave_type'],
        data['start_date'],  data['end_date'],
    ))


def update_status(request_id: int, company_id: int,
                  status: str, reviewed_by: int = None, notes: str = ''):
    """Update leave request status.
    Note: reviewed_by, reviewed_at, review_notes columns don't exist in current db
    """
    mutate("""
        UPDATE leave_requests
        SET status=%s
        WHERE id=%s AND company_id=%s
    """, (status, request_id, company_id))

    # Update leave balance if approved
    if status == 'Approved':
        row = query("""
            SELECT company_id, employee_id, start_date, end_date,
                   DATEDIFF(end_date, start_date) + 1 AS days_requested
            FROM leave_requests 
            WHERE id=%s
        """, (request_id,), one=True)
        if row:
            # All leave types contribute to annual_used (unified tracking per schema)
            yr = row['start_date'].year
            
            mutate("""
                INSERT INTO leave_balances
                  (company_id, employee_id, year, annual_used)
                VALUES(%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE annual_used = annual_used + VALUES(annual_used)
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