from models.db import query, mutate
from datetime import datetime


def get_compensation(employee_id: int, company_id: int):
    """Get employee base compensation (basic salary)"""
    return query("""
        SELECT id, employee_id, company_id, basic_salary, currency, created_at
        FROM compensation
        WHERE employee_id=%s AND company_id=%s
        ORDER BY created_at DESC LIMIT 1
    """, (employee_id, company_id), one=True)


def save_compensation(company_id: int, employee_id: int, data: dict):
    """Save employee base compensation (basic salary only)"""
    existing = get_compensation(employee_id, company_id)
    if existing:
        mutate("""
            UPDATE compensation SET
              basic_salary=%s, currency=%s
            WHERE id=%s
        """, (
            data.get('basic_salary', 0),
            data.get('currency', 'USD'),
            existing['id'],
        ))
    else:
        mutate("""
            INSERT INTO compensation
              (company_id, employee_id, basic_salary, currency)
            VALUES(%s, %s, %s, %s)
        """, (
            company_id,
            employee_id,
            data.get('basic_salary', 0),
            data.get('currency', 'USD'),
        ))


def get_runs(company_id: int, pay_period: str = None):
    if pay_period:
        return query("""
            SELECT pr.*, e.first_name, e.last_name, e.employee_code,
                   d.name AS dept_name
            FROM   payroll_runs pr
            JOIN   employees_core e ON e.id = pr.employee_id
            LEFT JOIN departments d ON d.id = e.department_id
            WHERE  pr.company_id=%s AND pr.pay_period=%s
            ORDER BY e.first_name
        """, (company_id, pay_period))
    return query("""
        SELECT pr.*, e.first_name, e.last_name, e.employee_code
        FROM   payroll_runs pr
        JOIN   employees_core e ON e.id = pr.employee_id
        WHERE  pr.company_id=%s
        ORDER BY pr.pay_period DESC, e.first_name
        LIMIT 200
    """, (company_id,))


def upsert_run(company_id: int, employee_id: int, pay_period: str,
               payload: dict) -> int:
    """Insert or update payroll run - uses schema_complete.sql columns."""
    return mutate("""
        INSERT INTO payroll_runs
          (company_id, employee_id, pay_period, basic_salary, gross_salary,
           overtime_hours, overtime_amount, prorated_salary,
           housing_allowance, transport_allowance, meal_allowance,
           performance_bonus, income_tax, social_security, 
           health_insurance, other_deductions, net_salary, status, notes)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
          basic_salary=VALUES(basic_salary),
          gross_salary=VALUES(gross_salary),
          overtime_hours=VALUES(overtime_hours),
          overtime_amount=VALUES(overtime_amount),
          prorated_salary=VALUES(prorated_salary),
          housing_allowance=VALUES(housing_allowance),
          transport_allowance=VALUES(transport_allowance),
          meal_allowance=VALUES(meal_allowance),
          performance_bonus=VALUES(performance_bonus),
          income_tax=VALUES(income_tax),
          social_security=VALUES(social_security),
          health_insurance=VALUES(health_insurance),
          other_deductions=VALUES(other_deductions),
          net_salary=VALUES(net_salary),
          status=VALUES(status),
          notes=VALUES(notes)
    """, (
        company_id, employee_id, pay_period,
        payload.get('basic_salary', 0),
        payload.get('gross_salary', 0),
        payload.get('overtime_hours', 0),
        payload.get('overtime_amount', 0),
        payload.get('prorated_salary', 0),
        payload.get('housing_allowance', 0),
        payload.get('transport_allowance', 0),
        payload.get('meal_allowance', 0),
        payload.get('performance_bonus', 0),
        payload.get('income_tax', 0),
        payload.get('social_security', 0),
        payload.get('health_insurance', 0),
        payload.get('other_deductions', 0),
        payload.get('net_salary', 0),
        payload.get('status', 'Draft'),
        payload.get('notes', ''),
    ))


def pending_count(company_id: int) -> int:
    row = query(
        "SELECT COUNT(*) AS cnt FROM payroll_runs "
        "WHERE company_id=%s AND status IN ('Draft','Pending')",
        (company_id,), one=True
    )
    return row['cnt'] if row else 0


def average_net_salary(company_id: int):
    """Get average net salary from recent payroll runs"""
    row = query("""
        SELECT AVG(p.net_salary) AS avg_net
        FROM payroll_runs p
        JOIN employees_core e ON e.id = p.employee_id
        WHERE p.company_id=%s AND e.status='Active' AND p.status IN ('Approved','Finalized')
        AND p.created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
    """, (company_id,), one=True)
    v = row['avg_net'] if row else None
    return float(v) if v else 0.0