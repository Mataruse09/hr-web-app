"""
Enhanced Payroll Calculation Service - Professional payroll processing
"""
from models.db import query, mutate
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# Tax configuration (can be made configurable per company)
TAX_RATES = {
    'income_tax_rate': 0.15,  # 15%
    'social_security_rate': 0.08,  # 8%
    'health_insurance_rate': 0.05,  # 5%
}

OVERTIME_MULTIPLIER = 1.5  # 1.5x for overtime


def calculate_working_days(year: int, month: int) -> int:
    """Calculate number of working days in a month (approx 22 per month)."""
    return 22


def calculate_payroll(company_id: int, employee_id: int, pay_period: str) -> dict:
    """
    Calculate complete payroll for an employee.
    pay_period format: "2026-01" (YYYY-MM)
    """
    try:
        # Get employee compensation
        compensation = query("""
            SELECT * FROM compensation
            WHERE company_id = %s AND employee_id = %s
        """, (company_id, employee_id), one=True)
        
        if not compensation:
            logger.warning(f"No compensation found for employee {employee_id}")
            return None
        
        basic_salary = compensation.get('basic_salary', 0)
        
        # Get attendance for the month
        year, month = pay_period.split('-')
        attendance_records = query("""
            SELECT * FROM attendance
            WHERE company_id = %s AND employee_id = %s
            AND EXTRACT(YEAR FROM work_date) = %s
            AND EXTRACT(MONTH FROM work_date) = %s
        """, (company_id, employee_id, int(year), int(month)))
        
        # Calculate working days and overtime
        working_days = calculate_working_days(int(year), int(month))
        actual_working_days = len([a for a in attendance_records if a.get('status') == 'Present'])
        overtime_hours = sum([a.get('working_hours', 0) for a in attendance_records if a.get('working_hours', 0) > 8]) if attendance_records else 0
        
        # Calculate proration (if employee didn't work full month)
        proration_factor = actual_working_days / working_days if working_days > 0 else 1.0
        
        # ===== EARNINGS =====
        basic_salary_calc = basic_salary * proration_factor
        
        # Allowances
        housing_allowance = (basic_salary * 0.15) * proration_factor  # 15% of basic
        transport_allowance = (basic_salary * 0.10) * proration_factor  # 10% of basic
        meal_allowance = (basic_salary * 0.05) * proration_factor  # 5% of basic
        
        # Overtime calculation (1.5x for hours beyond 8)
        daily_rate = basic_salary / working_days
        hourly_rate = daily_rate / 8
        overtime_amount = overtime_hours * hourly_rate * OVERTIME_MULTIPLIER
        
        # Performance bonus (0-5% based on appraisal, hardcoded for now)
        performance_bonus = basic_salary * 0.03  # 3% bonus
        
        # Gross salary
        gross_salary = (
            basic_salary_calc + 
            housing_allowance + 
            transport_allowance + 
            meal_allowance + 
            overtime_amount + 
            performance_bonus
        )
        
        # ===== DEDUCTIONS =====
        # Tax calculations
        income_tax = gross_salary * TAX_RATES['income_tax_rate']
        social_security = gross_salary * TAX_RATES['social_security_rate']
        health_insurance = gross_salary * TAX_RATES['health_insurance_rate']
        
        # Other deductions (can be specific to employee)
        other_deductions = 0  # Can be customized
        
        # Total deductions
        total_deductions = (
            income_tax + 
            social_security + 
            health_insurance + 
            other_deductions
        )
        
        # ===== NET SALARY =====
        net_salary = gross_salary - total_deductions
        
        payroll_data = {
            'employee_id': employee_id,
            'company_id': company_id,
            'pay_period': pay_period,
            'basic_salary': round(basic_salary_calc, 2),
            'housing_allowance': round(housing_allowance, 2),
            'transport_allowance': round(transport_allowance, 2),
            'meal_allowance': round(meal_allowance, 2),
            'overtime_hours': round(overtime_hours, 2),
            'overtime_amount': round(overtime_amount, 2),
            'performance_bonus': round(performance_bonus, 2),
            'gross_salary': round(gross_salary, 2),
            'income_tax': round(income_tax, 2),
            'social_security': round(social_security, 2),
            'health_insurance': round(health_insurance, 2),
            'other_deductions': round(other_deductions, 2),
            'net_salary': round(net_salary, 2),
            'proration_factor': round(proration_factor, 4),
            'status': 'Draft',
        }
        
        logger.info(f"Payroll calculated for employee {employee_id}: Net=${net_salary}")
        return payroll_data
    
    except Exception as e:
        logger.error(f"Payroll calculation failed: {e}")
        return None


def create_payroll_run(company_id: int, employee_id: int, pay_period: str, calculated_data: dict):
    """Create a payroll run record."""
    try:
        mutate("""
            INSERT INTO payroll_runs (
                company_id, employee_id, pay_period,
                basic_salary, housing_allowance, transport_allowance, meal_allowance,
                overtime_hours, overtime_amount, performance_bonus, gross_salary,
                income_tax, social_security, health_insurance, other_deductions, net_salary,
                status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            basic_salary = VALUES(basic_salary),
                housing_allowance = VALUES(housing_allowance),
                transport_allowance = VALUES(transport_allowance),
                meal_allowance = VALUES(meal_allowance),
                overtime_hours = VALUES(overtime_hours),
                overtime_amount = VALUES(overtime_amount),
                performance_bonus = VALUES(performance_bonus),
                gross_salary = VALUES(gross_salary),
                income_tax = VALUES(income_tax),
                social_security = VALUES(social_security),
                health_insurance = VALUES(health_insurance),
                other_deductions = VALUES(other_deductions),
                net_salary = VALUES(net_salary)
        """, (
            company_id, employee_id, pay_period,
            calculated_data['basic_salary'], calculated_data['housing_allowance'],
            calculated_data['transport_allowance'], calculated_data['meal_allowance'],
            calculated_data['overtime_hours'], calculated_data['overtime_amount'],
            calculated_data['performance_bonus'], calculated_data['gross_salary'],
            calculated_data['income_tax'], calculated_data['social_security'],
            calculated_data['health_insurance'], calculated_data['other_deductions'],
            calculated_data['net_salary'], 'Draft', datetime.utcnow()
        ))
        return True
    except Exception as e:
        logger.error(f"Payroll creation failed: {e}")
        return False


def approve_payroll(payroll_id: int, approved_by: int):
    """Approve a payroll run."""
    try:
        mutate("""
            UPDATE payroll_runs
            SET status = 'Approved', approved_by = %s, approved_at = %s
            WHERE id = %s
        """, (approved_by, datetime.utcnow(), payroll_id))
        logger.info(f"Payroll {payroll_id} approved by user {approved_by}")
        return True
    except Exception as e:
        logger.error(f"Payroll approval failed: {e}")
        return False


def get_payroll_summary(company_id: int, pay_period: str) -> dict:
    """Get payroll summary for a period."""
    try:
        payrolls = query("""
            SELECT 
                COUNT(*) as total_employees,
                COALESCE(SUM(gross_salary), 0) as total_gross,
                COALESCE(SUM(net_salary), 0) as total_net,
                COALESCE(SUM(income_tax), 0) as total_tax,
                COALESCE(SUM(overtime_amount), 0) as total_overtime
            FROM payroll_runs
            WHERE company_id = %s AND pay_period = %s
        """, (company_id, pay_period), one=True)
        
        return payroll_data if payroll_data else {}
    except Exception as e:
        logger.error(f"Payroll summary failed: {e}")
        return {}
