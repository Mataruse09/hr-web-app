from models.db import query, mutate
from datetime import date
import logging
import traceback

logger = logging.getLogger(__name__)


def get_by_date(company_id: int, work_date: str):
    try:
        return query("""
            SELECT a.*, e.first_name, e.last_name, e.employee_code, d.name AS dept
            FROM   attendance a
            JOIN   employees_core e ON e.id = a.employee_id
            LEFT JOIN departments d ON d.id = e.department_id
            WHERE  a.company_id=%s AND a.work_date=%s
            ORDER BY e.first_name
        """, (company_id, work_date))
    except Exception as e:
        logger.error(f"Error getting attendance for date {work_date}: {e}")
        return []


def get_logs(company_id: int, from_date: str, to_date: str, emp_id=None):
    try:
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
    except Exception as e:
        logger.error(f"Error getting attendance logs: {e}")
        return []


def upsert(company_id: int, employee_id: int, work_date: str,
           check_in, check_out, status: str, notes: str, recorded_by: int):
    """Insert or update an attendance record with proper time validation and cross-midnight handling."""

    hours = None

    if check_in and check_out:
        from datetime import datetime, timedelta

        fmt = "%H:%M"
        try:
            ci_str = str(check_in)[:5]  # "HH:MM"
            co_str = str(check_out)[:5]

            ci = datetime.strptime(ci_str, fmt)
            co = datetime.strptime(co_str, fmt)

            diff = (co - ci).total_seconds() / 3600

            # Handle cross-midnight shifts (check_out < check_in)
            if diff < 0:
                diff = (24 + diff)  # Adds 24 hours for overnight shifts
                if diff > 0:
                    hours = round(diff, 2)
            elif diff > 0:
                hours = round(diff, 2)
            # If diff == 0, hours stays None (same time)

        except Exception as e:
            # Log error but don't fail - NULL hours indicates data issue
            import logging
            logging.warning(f"Attendance time parse error: {e}")
            hours = None

    mutate("""
        INSERT INTO attendance
          (company_id, employee_id, work_date, check_in, check_out, status,
           working_hours, notes, recorded_by)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          check_in = VALUES(check_in),
          check_out = VALUES(check_out),
          status = VALUES(status),
          working_hours = VALUES(working_hours),
          notes = VALUES(notes),
          recorded_by = VALUES(recorded_by)
    """, (
        company_id,
        employee_id,
        work_date,
        check_in or None,
        check_out or None,
        status,
        hours,
        (notes or None),
        recorded_by
    ))


def today_summary(company_id: int, today: str):
    row = query("""
        SELECT
          SUM(CASE WHEN status IN ('Present','Work From Home','Half-Day') THEN 1 ELSE 0 END) AS present,
          SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent,
          SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) AS late,
          COUNT(*) AS total
        FROM attendance
        WHERE company_id=%s AND work_date=%s
    """, (company_id, today), one=True)

    return row or {'present': 0, 'absent': 0, 'late': 0, 'total': 0}


def monthly_present_days(company_id: int, employee_id: int,
                         year: int, month: int) -> int:
    row = query("""
        SELECT COUNT(*) AS cnt FROM attendance
        WHERE company_id=%s AND employee_id=%s
          AND EXTRACT(YEAR FROM work_date)=%s
          AND EXTRACT(MONTH FROM work_date)=%s
          AND status IN ('Present','Late','Work From Home','Half-Day')
    """, (company_id, employee_id, year, month), one=True)

    return row['cnt'] if row else 0