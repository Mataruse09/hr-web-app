from models.db import query, mutate
from datetime import datetime


def get_compensation(employee_id: int, company_id: int):
    return query("""
        SELECT * FROM compensation
        WHERE employee_id=%s AND company_id=%s
        ORDER BY effective_date DESC LIMIT 1
    """, (employee_id, company_id), one=True)


def save_compensation(company_id: int, employee_id: int, data: dict):
    existing = get_compensation(employee_id, company_id)
    if existing:
        mutate("""
            UPDATE compensation SET
              basic_salary=%s, housing_allowance=%s, transport_allowance=%s,
              meal_allowance=%s, other_allowances=%s, income_tax_rate=%s,
              social_insurance=%s, health_insurance=%s, other_deductions=%s,
              currency=%s, effective_date=%s
            WHERE id=%s
        """, (
            data['basic_salary'],  data.get('housing_allowance', 0),
            data.get('transport_allowance', 0), data.get('meal_allowance', 0),
            data.get('other_allowances', 0),    data.get('income_tax_rate', 15),
            data.get('social_insurance', 0),    data.get('health_insurance', 0),
            data.get('other_deductions', 0),    data.get('currency', 'USD'),
            data.get('effective_date'),          existing['id'],
        ))
    else:
        mutate("""
            INSERT INTO compensation
              (company_id,employee_id,basic_salary,housing_allowance,
               transport_allowance,meal_allowance,other_allowances,
               income_tax_rate,social_insurance,health_insurance,
               other_deductions,currency,effective_date)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            company_id, employee_id,
            data['basic_salary'],  data.get('housing_allowance', 0),
            data.get('transport_allowance', 0), data.get('meal_allowance', 0),
            data.get('other_allowances', 0),    data.get('income_tax_rate', 15),
            data.get('social_insurance', 0),    data.get('health_insurance', 0),
            data.get('other_deductions', 0),    data.get('currency', 'USD'),
            data.get('effective_date'),
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
    return mutate("""
        INSERT INTO payroll_runs
          (company_id,employee_id,pay_period,basic_salary,total_allowances,
           gross_salary,bonus,income_tax,total_deductions,net_salary,
           working_days,present_days,status,processed_by,processed_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (company_id, employee_id, pay_period)
        DO UPDATE SET
          basic_salary=EXCLUDED.basic_salary,
          total_allowances=EXCLUDED.total_allowances,
          gross_salary=EXCLUDED.gross_salary,
          bonus=EXCLUDED.bonus,
          income_tax=EXCLUDED.income_tax,
          total_deductions=EXCLUDED.total_deductions,
          net_salary=EXCLUDED.net_salary,
          working_days=EXCLUDED.working_days,
          present_days=EXCLUDED.present_days,
          status=EXCLUDED.status,
          processed_by=EXCLUDED.processed_by,
          processed_at=EXCLUDED.processed_at
    """, (
        company_id, employee_id, pay_period,
        payload['basic_salary'],  payload['total_allowances'],
        payload['gross_salary'],  payload['bonus'],
        payload['income_tax'],    payload['total_deductions'],
        payload['net_salary'],    payload['working_days'],
        payload['present_days'],  payload['status'],
        payload['processed_by'],  payload['processed_at'],
    ))


def pending_count(company_id: int) -> int:
    row = query(
        "SELECT COUNT(*) AS cnt FROM payroll_runs "
        "WHERE company_id=%s AND status IN ('Draft','Pending')",
        (company_id,), one=True
    )
    return row['cnt'] if row else 0


def average_net_salary(company_id: int):
    row = query("""
        SELECT AVG(c.basic_salary +
                   c.housing_allowance + c.transport_allowance +
                   c.meal_allowance + c.other_allowances -
                   (c.basic_salary * c.income_tax_rate / 100) -
                   c.social_insurance - c.health_insurance - c.other_deductions
               ) AS avg_net
        FROM compensation c
        JOIN employees_core e ON e.id = c.employee_id
        WHERE c.company_id=%s AND e.status='Active'
    """, (company_id,), one=True)
    v = row['avg_net'] if row else None
    return float(v) if v else 0.0