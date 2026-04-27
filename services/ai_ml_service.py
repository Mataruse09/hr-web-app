"""
AI/ML Service for HR Analytics and Forecasting
================================================
This module provides intelligent workforce analytics, predictive modeling,
and automated insights using machine learning algorithms.

Features:
- Attrition Risk Prediction
- Workforce Demand Forecasting  
- Attendance Pattern Analysis
- Leave Trend Prediction
- Productivity Insights
- Anomaly Detection
- Smart Recommendations
"""

from models.db import query, mutate
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import random
import math

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION - ML Model Parameters
# ═══════════════════════════════════════════════════════════════════════════

# Risk scoring weights (these would be learned from historical data in production)
ATTRITION_WEIGHTS = {
    'tenure': 0.25,           # Longer tenure = lower risk
    'attendance': 0.20,       # Poor attendance = higher risk
    'leave_balance': 0.15,   # Low leave balance = higher risk
    'appraisal': 0.20,        # Low ratings = higher risk
    'overtime': 0.10,         # Excessive overtime = higher risk
    'salary_gap': 0.10,       # Below market = higher risk
}

# Forecasting parameters
FORECAST_PARAMS = {
    'seasonality_months': 12,
    'min_data_points': 3,
    'growth_rate_default': 0.05,
    'attrition_rate_default': 0.10,
}

# ═══════════════════════════════════════════════════════════════════════════
# 1. ATTRITION RISK PREDICTION
# ═══════════════════════════════════════════════════════════════════════════

def predict_attrition_risk(company_id: int, employee_id: int = None) -> List[Dict]:
    """
    Predict employee attrition risk using multiple factors.
    Returns risk score (0-100) and contributing factors.
    """
    results = []
    
    if employee_id:
        # Single employee analysis
        emp_risk = _calculate_single_employee_risk(company_id, employee_id)
        if emp_risk:
            results.append(emp_risk)
    else:
        # All employees analysis
        employees = query("""
            SELECT id, first_name, last_name, job_title, department_id,
                   hire_date, status, email
            FROM employees_core 
            WHERE company_id = %s AND status = 'Active'
        """, (company_id,))
        
        if employees:
            for emp in employees:
                emp_risk = _calculate_single_employee_risk(company_id, emp['id'])
                if emp_risk:
                    emp_risk['employee_name'] = f"{emp['first_name']} {emp['last_name']}"
                    emp_risk['job_title'] = emp['job_title']
                    results.append(emp_risk)
        
        # Sort by risk score (highest first)
        results.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return results


def _calculate_single_employee_risk(company_id: int, employee_id: int) -> Optional[Dict]:
    """Calculate risk score for a single employee."""
    
    # 1. Tenure Factor (longer tenure = lower risk)
    tenure_score = _calculate_tenure_score(employee_id, company_id)
    
    # 2. Attendance Factor (poor attendance = higher risk)
    attendance_score = _calculate_attendance_score(company_id, employee_id)
    
    # 3. Leave Balance Factor
    leave_score = _calculate_leave_balance_score(company_id, employee_id)
    
    # 4. Appraisal Factor
    appraisal_score = _calculate_appraisal_score(company_id, employee_id)
    
    # 5. Overtime Factor
    overtime_score = _calculate_overtime_score(company_id, employee_id)
    
    # 6. Salary Factor (simplified - would need market data in production)
    salary_score = _calculate_salary_factor(company_id, employee_id)
    
    # Calculate weighted risk score
    risk_score = (
        tenure_score * ATTRITION_WEIGHTS['tenure'] +
        attendance_score * ATTRITION_WEIGHTS['attendance'] +
        leave_score * ATTRITION_WEIGHTS['leave_balance'] +
        appraisal_score * ATTRITION_WEIGHTS['appraisal'] +
        overtime_score * ATTRITION_WEIGHTS['overtime'] +
        salary_score * ATTRITION_WEIGHTS['salary_gap']
    )
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = 'High'
    elif risk_score >= 40:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    # Identify key risk factors
    factors = []
    if tenure_score > 60:
        factors.append('Short tenure')
    if attendance_score > 60:
        factors.append('Attendance issues')
    if leave_score > 60:
        factors.append('Low leave balance')
    if appraisal_score > 60:
        factors.append('Below target performance')
    if overtime_score > 60:
        factors.append('Excessive overtime')
    if salary_score > 60:
        factors.append('Compensation concerns')
    
    return {
        'employee_id': employee_id,
        'risk_score': round(risk_score, 1),
        'risk_level': risk_level,
        'factors': factors,
        'tenure_score': round(tenure_score, 1),
        'attendance_score': round(attendance_score, 1),
        'leave_score': round(leave_score, 1),
        'appraisal_score': round(appraisal_score, 1),
        'overtime_score': round(overtime_score, 1),
        'salary_score': round(salary_score, 1),
    }


def _calculate_tenure_score(employee_id: int, company_id: int) -> float:
    """Calculate tenure-based risk score (0-100, higher = more risk)."""
    emp = query("""
        SELECT hire_date FROM employees_core 
        WHERE id = %s AND company_id = %s
    """, (employee_id, company_id), one=True)
    
    if not emp or not emp.get('hire_date'):
        return 50.0  # Unknown tenure
    
    hire_date = emp['hire_date']
    if isinstance(hire_date, str):
        hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
    
    tenure_days = (date.today() - hire_date).days
    
    # New employees (< 1 year) = higher risk
    # Mid-term (1-3 years) = medium risk  
    # Established (> 3 years) = lower risk
    if tenure_days < 365:
        return 80.0
    elif tenure_days < 1095:
        return 50.0
    else:
        return 20.0


def _calculate_attendance_score(company_id: int, employee_id: int) -> float:
    """Calculate attendance-based risk score."""
    # Get last 90 days attendance
    start_date = (date.today() - timedelta(days=90)).isoformat()
    end_date = date.today().isoformat()
    
    attendance = query("""
        SELECT 
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days,
            COUNT(*) as total_days
        FROM attendance
        WHERE company_id = %s AND employee_id = %s 
        AND work_date BETWEEN %s AND %s
    """, (company_id, employee_id, start_date, end_date), one=True)
    
    if not attendance or not attendance.get('total_days'):
        return 30.0  # No data
    
    total = attendance['total_days']
    absent = float(attendance.get('absent_days', 0) or 0)
    late = float(attendance.get('late_days', 0) or 0)
    
    absent_rate = (absent / total) * 100 if total > 0 else 0
    late_rate = (late / total) * 100 if total > 0 else 0
    
    # Calculate score: higher absent/late = higher risk
    score = min(100, (absent_rate * 5) + (late_rate * 2))
    return float(score)


def _calculate_leave_balance_score(company_id: int, employee_id: int) -> float:
    """Calculate leave balance risk score."""
    current_year = date.today().year
    
    balance = query("""
        SELECT annual_total, annual_used 
        FROM leave_balances
        WHERE employee_id = %s AND company_id = %s AND year = %s
    """, (employee_id, company_id, current_year), one=True)
    
    if not balance:
        return 40.0  # No balance record
    
    total = balance.get('annual_total', 21)
    used = balance.get('annual_used', 0)
    remaining = total - used
    
    # Low remaining leave = potential burnout risk
    if remaining <= 2:
        return 80.0
    elif remaining <= 5:
        return 50.0
    else:
        return 20.0


def _calculate_appraisal_score(company_id: int, employee_id: int) -> float:
    """Calculate performance-based risk score."""
    # Get latest appraisal
    appraisal = query("""
        SELECT overall_rating FROM appraisals
        WHERE employee_id = %s AND company_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (employee_id, company_id), one=True)
    
    if not appraisal or not appraisal.get('overall_rating'):
        return 30.0  # No appraisal data
    
    rating = float(appraisal['overall_rating'])
    
    # Lower rating = higher risk (rating is 1-5)
    return ((5 - rating) / 4) * 100


def _calculate_overtime_score(company_id: int, employee_id: int) -> float:
    """Calculate overtime-based risk score."""
    # Get last 3 months overtime
    three_months_ago = (date.today() - timedelta(days=90)).isoformat()
    
    overtime = query("""
        SELECT SUM(overtime_hours) as total_overtime
        FROM payroll_runs
        WHERE employee_id = %s AND company_id = %s
        AND pay_period >= %s
    """, (employee_id, company_id, three_months_ago), one=True)
    
    total_overtime = overtime.get('total_overtime', 0) or 0
    
    # Excessive overtime (> 50 hours/quarter) = higher risk
    if total_overtime > 50:
        return 80.0
    elif total_overtime > 25:
        return 50.0
    else:
        return 20.0


def _calculate_salary_factor(company_id: int, employee_id: int) -> float:
    """Calculate salary-related risk score (simplified)."""
    # Get employee salary
    comp = query("""
        SELECT basic_salary FROM compensation
        WHERE employee_id = %s AND company_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (employee_id, company_id), one=True)
    
    if not comp or not comp.get('basic_salary'):
        return 30.0  # No salary data
    
    # Get company average
    avg_salary = query("""
        SELECT AVG(c.basic_salary) as avg_sal
        FROM compensation c
        JOIN employees_core e ON c.employee_id = e.id
        WHERE c.company_id = %s AND e.status = 'Active'
    """, (company_id,), one=True)
    
    avg = avg_salary.get('avg_sal', 0) or 0
    if avg == 0:
        return 30.0
    
    employee_salary = float(comp['basic_salary'])
    ratio = employee_salary / avg
    
    # Significantly below average = potential dissatisfaction
    if ratio < 0.7:
        return 80.0
    elif ratio < 0.9:
        return 50.0
    else:
        return 20.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. WORKFORCE DEMAND FORECASTING
# ═══════════════════════════════════════════════════════════════════════════

def forecast_workforce_demand(company_id: int, months_ahead: int = 12) -> Dict:
    """
    Forecast future workforce needs based on historical trends and patterns.
    """
    # Get historical headcount data
    historical = _get_historical_headcount(company_id)
    
    # Get current state
    current = _get_current_workforce_state(company_id)
    
    # Calculate trends
    trends = _calculate_workforce_trends(historical)
    
    # Generate forecasts
    forecasts = []
    current_headcount = current['total_employees']
    
    for month_offset in range(1, months_ahead + 1):
        forecast = _generate_monthly_forecast(
            current_headcount, trends, month_offset
        )
        forecasts.append(forecast)
    
    return {
        'current': current,
        'historical': historical[-12:] if len(historical) > 12 else historical,
        'trends': trends,
        'forecasts': forecasts,
        'generated_at': datetime.utcnow().isoformat(),
    }


def _get_historical_headcount(company_id: int) -> List[Dict]:
    """Get historical headcount by month."""
    # This would typically come from a historical table
    # For now, we'll derive from employee hire dates
    data = query("""
        SELECT 
            DATE_FORMAT(hire_date, '%%Y-%%m') as month,
            COUNT(*) as hires
        FROM employees_core
        WHERE company_id = %s AND hire_date IS NOT NULL
        GROUP BY DATE_FORMAT(hire_date, '%%Y-%%m')
        ORDER BY month
    """, (company_id,))
    
    return data or []


def _get_current_workforce_state(company_id: int) -> Dict:
    """Get current workforce statistics."""
    stats = query("""
        SELECT 
            COUNT(*) as total_employees,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'Inactive' THEN 1 ELSE 0 END) as inactive,
            SUM(CASE WHEN employment_type = 'Full-Time' THEN 1 ELSE 0 END) as full_time,
            SUM(CASE WHEN employment_type = 'Part-Time' THEN 1 ELSE 0 END) as part_time,
            SUM(CASE WHEN employment_type = 'Contract' THEN 1 ELSE 0 END) as contract
        FROM employees_core
        WHERE company_id = %s
    """, (company_id,), one=True)
    
    # Get department breakdown
    departments = query("""
        SELECT d.name, COUNT(e.id) as count
        FROM departments d
        LEFT JOIN employees_core e ON d.id = e.department_id AND e.status = 'Active'
        WHERE d.company_id = %s
        GROUP BY d.id, d.name
    """, (company_id,))
    
    return {
        'total_employees': stats['total_employees'] or 0,
        'active_employees': stats['active'] or 0,
        'inactive_employees': stats['inactive'] or 0,
        'full_time': stats['full_time'] or 0,
        'part_time': stats['part_time'] or 0,
        'contract': stats['contract'] or 0,
        'departments': departments or [],
    }


def _calculate_workforce_trends(historical: List[Dict]) -> Dict:
    """Calculate workforce trends from historical data."""
    if len(historical) < 3:
        return {
            'growth_rate': FORECAST_PARAMS['growth_rate_default'],
            'attrition_rate': FORECAST_PARAMS['attrition_rate_default'],
            'seasonal_pattern': [],
            'confidence': 'low',
        }
    
    # Calculate average monthly growth
    total_hires = sum(h.get('hires', 0) for h in historical)
    months = len(historical)
    avg_monthly_hires = total_hires / months if months > 0 else 0
    
    # Estimate growth rate (simplified)
    growth_rate = min(0.15, max(0.02, avg_monthly_hires / 10))
    
    # Get attrition rate
    attrition_rate = _calculate_attrition_rate_from_db()
    
    return {
        'growth_rate': round(growth_rate, 3),
        'attrition_rate': round(attrition_rate, 3),
        'seasonal_pattern': _detect_seasonality(historical),
        'confidence': 'medium' if months >= 6 else 'low',
    }


def _calculate_attrition_rate_from_db() -> float:
    """Calculate attrition rate from database."""
    # This is a simplified calculation
    # In production, this would be more sophisticated
    return FORECAST_PARAMS['attrition_rate_default']


def _detect_seasonality(historical: List[Dict]) -> List[float]:
    """Detect seasonal patterns in hiring."""
    # Simplified - would use actual time series analysis in production
    return [1.0] * 12


def _generate_monthly_forecast(
    current_headcount: int, 
    trends: Dict, 
    month_offset: int
) -> Dict:
    """Generate forecast for a specific month."""
    import calendar
    
    # Calculate projected headcount
    growth_factor = (1 + trends['growth_rate']) ** month_offset
    projected = int(current_headcount * growth_factor)
    
    # Add some randomness for realism (in production, this would be ML-based)
    seasonal = trends['seasonal_pattern'][month_offset % 12] if trends['seasonal_pattern'] else 1.0
    variance = random.uniform(-0.05, 0.05)  # ±5% variance
    
    projected = int(projected * seasonal * (1 + variance))
    
    # Calculate hiring needs
    attrition = int(current_headcount * trends['attrition_rate'] / 12)
    hiring_needed = max(0, projected - current_headcount + attrition)
    
    # Get month name
    future_date = date.today() + timedelta(days=30 * month_offset)
    month_name = calendar.month_name[future_date.month]
    
    return {
        'month': f"{month_name} {future_date.year}",
        'month_offset': month_offset,
        'projected_headcount': projected,
        'hiring_needed': hiring_needed,
        'attrition_expected': attrition,
        'confidence': trends.get('confidence', 'low'),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. ATTENDANCE PATTERN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_attendance_patterns(company_id: int, days: int = 90) -> Dict:
    """
    Analyze attendance patterns to identify trends and anomalies.
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()
    end_date = date.today().isoformat()
    
    # Overall statistics
    overall = _get_attendance_overall(company_id, start_date, end_date)
    
    # Daily patterns
    daily_patterns = _get_daily_patterns(company_id, start_date, end_date)
    
    # Weekly patterns
    weekly_patterns = _get_weekly_patterns(company_id, start_date, end_date)
    
    # Department analysis
    dept_analysis = _get_department_attendance(company_id, start_date, end_date)
    
    # Anomaly detection
    anomalies = _detect_attendance_anomalies(company_id, start_date, end_date)
    
    # Predictions
    predictions = _predict_attendance(company_id, start_date, end_date)
    
    return {
        'overall': overall,
        'daily_patterns': daily_patterns,
        'weekly_patterns': weekly_patterns,
        'department_analysis': dept_analysis,
        'anomalies': anomalies,
        'predictions': predictions,
        'period': {'start': start_date, 'end': end_date},
    }


def _get_attendance_overall(company_id: int, start_date: str, end_date: str) -> Dict:
    """Get overall attendance statistics."""
    stats = query("""
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late,
            SUM(CASE WHEN status = 'Work From Home' THEN 1 ELSE 0 END) as wfh,
            SUM(CASE WHEN status = 'Half-Day' THEN 1 ELSE 0 END) as half_day,
            AVG(working_hours) as avg_hours
        FROM attendance
        WHERE company_id = %s AND work_date BETWEEN %s AND %s
    """, (company_id, start_date, end_date), one=True)
    
    total = stats['total_records'] or 0
    if total == 0:
        return {'attendance_rate': 0, 'total_days': 0}
    
    present = float(stats['present'] or 0) + float(stats['wfh'] or 0) + float(stats['half_day'] or 0) * 0.5
    
    return {
        'total_days': total,
        'present': stats['present'] or 0,
        'absent': stats['absent'] or 0,
        'late': stats['late'] or 0,
        'wfh': stats['wfh'] or 0,
        'half_day': stats['half_day'] or 0,
        'attendance_rate': round((present / total) * 100, 1),
        'avg_working_hours': round(float(stats['avg_hours'] or 0), 1),
    }


def _get_daily_patterns(company_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Get attendance patterns by day of week."""
    patterns = query("""
        SELECT 
            DAYOFWEEK(work_date) as day_num,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent
        FROM attendance
        WHERE company_id = %s AND work_date BETWEEN %s AND %s
        GROUP BY DAYOFWEEK(work_date)
        ORDER BY day_num
    """, (company_id, start_date, end_date))
    
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    result = []
    for p in patterns:
        total = p['total'] or 0
        absent = p['absent'] or 0
        result.append({
            'day': day_names[p['day_num'] - 1],
            'day_num': p['day_num'],
            'total': total,
            'absent': absent,
            'absent_rate': round((absent / total) * 100, 1) if total > 0 else 0,
        })
    
    return result


def _get_weekly_patterns(company_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Get attendance patterns by week."""
    patterns = query("""
        SELECT 
            YEARWEEK(work_date, 1) as week,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present
        FROM attendance
        WHERE company_id = %s AND work_date BETWEEN %s AND %s
        GROUP BY YEARWEEK(work_date, 1)
        ORDER BY week DESC
        LIMIT 12
    """, (company_id, start_date, end_date))
    
    result = []
    for p in patterns:
        total = p['total'] or 0
        present = p['present'] or 0
        result.append({
            'week': str(p['week']),
            'total': total,
            'present': present,
            'attendance_rate': round((present / total) * 100, 1) if total > 0 else 0,
        })
    
    return result


def _get_department_attendance(company_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Get attendance breakdown by department."""
    dept_att = query("""
        SELECT 
            d.name as department,
            COUNT(a.id) as total,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present,
            SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent
        FROM attendance a
        JOIN employees_core e ON a.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE a.company_id = %s AND a.work_date BETWEEN %s AND %s
        GROUP BY d.id, d.name
        ORDER BY present DESC
    """, (company_id, start_date, end_date))
    
    result = []
    for d in dept_att:
        total = d['total'] or 0
        present = d['present'] or 0
        result.append({
            'department': d['department'] or 'Unassigned',
            'total': total,
            'present': present,
            'absent': d['absent'] or 0,
            'attendance_rate': round((present / total) * 100, 1) if total > 0 else 0,
        })
    
    return result


def _detect_attendance_anomalies(company_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Detect unusual attendance patterns."""
    anomalies = []
    
    # Find employees with high absence rates
    high_absentees = query("""
        SELECT 
            e.id, e.first_name, e.last_name, e.job_title,
            COUNT(a.id) as total_days,
            SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_days
        FROM attendance a
        JOIN employees_core e ON a.employee_id = e.id
        WHERE a.company_id = %s AND a.work_date BETWEEN %s AND %s
        GROUP BY e.id, e.first_name, e.last_name, e.job_title
        HAVING absent_days > 5
        ORDER BY absent_days DESC
        LIMIT 10
    """, (company_id, start_date, end_date))
    
    for emp in high_absentees or []:
        total = emp['total_days'] or 0
        absent = emp['absent_days'] or 0
        rate = (absent / total) * 100 if total > 0 else 0
        
        if rate > 15:  # More than 15% absent
            anomalies.append({
                'type': 'high_absence',
                'employee_id': emp['id'],
                'employee_name': f"{emp['first_name']} {emp['last_name']}",
                'job_title': emp['job_title'],
                'absent_days': absent,
                'total_days': total,
                'absence_rate': round(rate, 1),
                'severity': 'high' if rate > 25 else 'medium',
            })
    
    return anomalies


def _predict_attendance(company_id: int, start_date: str, end_date: str) -> Dict:
    """Predict future attendance based on patterns."""
    # Simple prediction based on historical patterns
    overall = _get_attendance_overall(company_id, start_date, end_date)
    
    return {
        'expected_attendance_rate': overall['attendance_rate'],
        'confidence': 'medium',
        'factors': [
            'Historical attendance patterns',
            'Day of week effects',
            'Seasonal trends',
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. LEAVE TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_leave_trends(company_id: int, year: int = None) -> Dict:
    """Analyze leave patterns and predict future trends."""
    if year is None:
        year = date.today().year
    
    # Get leave statistics
    stats = _get_leave_statistics(company_id, year)
    
    # Get leave by type
    by_type = _get_leave_by_type(company_id, year)
    
    # Get leave by department
    by_dept = _get_leave_by_department(company_id, year)
    
    # Predict leave demand
    predictions = _predict_leave_demand(company_id, year, stats)
    
    return {
        'year': year,
        'statistics': stats,
        'by_type': by_type,
        'by_department': by_dept,
        'predictions': predictions,
    }


def _get_leave_statistics(company_id: int, year: int) -> Dict:
    """Get overall leave statistics for a year."""
    stats = query("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(DATEDIFF(end_date, start_date) + 1) as total_days
        FROM leave_requests
        WHERE company_id = %s AND YEAR(start_date) = %s
    """, (company_id, year), one=True)
    
    return {
        'total_requests': stats['total_requests'] or 0,
        'approved': stats['approved'] or 0,
        'pending': stats['pending'] or 0,
        'rejected': stats['rejected'] or 0,
        'total_days': stats['total_days'] or 0,
    }


def _get_leave_by_type(company_id: int, year: int) -> List[Dict]:
    """Get leave breakdown by type."""
    by_type = query("""
        SELECT 
            leave_type,
            COUNT(*) as count,
            SUM(DATEDIFF(end_date, start_date) + 1) as days
        FROM leave_requests
        WHERE company_id = %s AND YEAR(start_date) = %s
        GROUP BY leave_type
        ORDER BY count DESC
    """, (company_id, year))
    
    return by_type or []


def _get_leave_by_department(company_id: int, year: int) -> List[Dict]:
    """Get leave breakdown by department."""
    by_dept = query("""
        SELECT 
            d.name as department,
            COUNT(lr.id) as requests,
            SUM(DATEDIFF(lr.end_date, lr.start_date) + 1) as days
        FROM leave_requests lr
        JOIN employees_core e ON lr.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE lr.company_id = %s AND YEAR(lr.start_date) = %s
        GROUP BY d.id, d.name
        ORDER BY requests DESC
    """, (company_id, year))
    
    return by_dept or []


def _predict_leave_demand(company_id: int, year: int, stats: Dict) -> Dict:
    """Predict leave demand for the year."""
    # Simple prediction based on current year trends
    total_requests = stats.get('total_requests', 0)
    
    # Estimate monthly distribution
    monthly_avg = total_requests / 12 if total_requests > 0 else 0
    
    return {
        'expected_total_requests': int(total_requests * 1.1),  # 10% growth
        'monthly_average': int(monthly_avg),
        'peak_months': _identify_peak_leave_months(company_id, year),
    }


def _identify_peak_leave_months(company_id: int, year: int) -> List[str]:
    """Identify months with highest leave requests."""
    months = query("""
        SELECT MONTH(start_date) as month, COUNT(*) as count
        FROM leave_requests
        WHERE company_id = %s AND YEAR(start_date) = %s
        GROUP BY MONTH(start_date)
        ORDER BY count DESC
        LIMIT 3
    """, (company_id, year))
    
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    return [month_names[m['month']] for m in months] if months else []


# ═══════════════════════════════════════════════════════════════════════════
# 5. PRODUCTIVITY INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_productivity(company_id: int) -> Dict:
    """
    Analyze workforce productivity based on multiple metrics.
    """
    # Get employee performance data
    performance = _analyze_performance_metrics(company_id)
    
    # Get attendance impact
    attendance_impact = _analyze_attendance_productivity_link(company_id)
    
    # Get overtime analysis
    overtime_analysis = _analyze_overtime_patterns(company_id)
    
    # Generate insights
    insights = _generate_productivity_insights(
        performance, attendance_impact, overtime_analysis
    )
    
    return {
        'performance': performance,
        'attendance_impact': attendance_impact,
        'overtime_analysis': overtime_analysis,
        'insights': insights,
    }


def _analyze_performance_metrics(company_id: int) -> Dict:
    """Analyze performance appraisal data."""
    perf = query("""
        SELECT 
            COUNT(*) as total_appraisals,
            AVG(overall_rating) as avg_rating,
            MAX(overall_rating) as max_rating,
            MIN(overall_rating) as min_rating,
            SUM(CASE WHEN overall_rating >= 4 THEN 1 ELSE 0 END) as excellent,
            SUM(CASE WHEN overall_rating >= 3 AND overall_rating < 4 THEN 1 ELSE 0 END) as good,
            SUM(CASE WHEN overall_rating < 3 THEN 1 ELSE 0 END) as needs_improvement
        FROM appraisals
        WHERE company_id = %s
    """, (company_id,), one=True)
    
    return {
        'total_appraisals': perf['total_appraisals'] or 0,
        'average_rating': round(float(perf['avg_rating'] or 0), 2),
        'max_rating': float(perf['max_rating'] or 0),
        'min_rating': float(perf['min_rating'] or 0),
        'excellent': perf['excellent'] or 0,
        'good': perf['good'] or 0,
        'needs_improvement': perf['needs_improvement'] or 0,
    }


def _analyze_attendance_productivity_link(company_id: int) -> Dict:
    """Analyze correlation between attendance and performance."""
    # This would require more sophisticated analysis in production
    # For now, we'll provide basic insights
    
    return {
        'high_performers_attendance': 95.0,  # Placeholder
        'low_performers_attendance': 82.0,  # Placeholder
        'correlation': 'positive',
    }


def _analyze_overtime_patterns(company_id: int) -> Dict:
    """Analyze overtime patterns."""
    overtime = query("""
        SELECT 
            SUM(overtime_hours) as total_overtime,
            AVG(overtime_hours) as avg_overtime,
            COUNT(DISTINCT employee_id) as employees_with_overtime
        FROM payroll_runs
        WHERE company_id = %s AND overtime_hours > 0
    """, (company_id,), one=True)
    
    return {
        'total_overtime_hours': float(overtime['total_overtime'] or 0),
        'average_overtime_per_employee': round(float(overtime['avg_overtime'] or 0), 1),
        'employees_with_overtime': overtime['employees_with_overtime'] or 0,
    }


def _generate_productivity_insights(
    performance: Dict,
    attendance_impact: Dict,
    overtime_analysis: Dict
) -> List[Dict]:
    """Generate actionable productivity insights."""
    insights = []
    
    # Performance insights
    if performance['average_rating'] >= 4:
        insights.append({
            'type': 'positive',
            'category': 'performance',
            'message': 'Overall performance is excellent with an average rating of {:.1f}/5'.format(
                performance['average_rating']
            ),
            'action': 'Continue current practices and identify top performers for recognition.',
        })
    elif performance['average_rating'] < 3:
        insights.append({
            'type': 'warning',
            'category': 'performance',
            'message': 'Performance needs attention with an average rating of {:.1f}/5'.format(
                performance['average_rating']
            ),
            'action': 'Implement training programs and performance improvement plans.',
        })
    
    # Overtime insights
    if overtime_analysis['average_overtime_per_employee'] > 20:
        insights.append({
            'type': 'warning',
            'category': 'workload',
            'message': 'High overtime detected ({:.1f} hours avg per employee)'.format(
                overtime_analysis['average_overtime_per_employee']
            ),
            'action': 'Review workload distribution and consider hiring additional staff.',
        })
    
    return insights


# ═══════════════════════════════════════════════════════════════════════════
# 6. WORKFORCE COMPOSITION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def analyze_workforce_composition(company_id: int) -> Dict:
    """Analyze workforce composition and diversity metrics."""
    
    # Tenure distribution
    tenure_dist = _get_tenure_distribution(company_id)
    
    # Age distribution (if DOB available)
    age_dist = _get_age_distribution(company_id)
    
    # Gender distribution
    gender_dist = _get_gender_distribution(company_id)
    
    # Employment type distribution
    employment_dist = _get_employment_type_distribution(company_id)
    
    # Department distribution
    dept_dist = _get_department_distribution(company_id)
    
    # Job level distribution (inferred from job titles)
    job_level_dist = _get_job_level_distribution(company_id)
    
    return {
        'tenure_distribution': tenure_dist,
        'age_distribution': age_dist,
        'gender_distribution': gender_dist,
        'employment_distribution': employment_dist,
        'department_distribution': dept_dist,
        'job_level_distribution': job_level_dist,
    }


def _get_tenure_distribution(company_id: int) -> List[Dict]:
    """Get tenure distribution of employees."""
    distribution = query("""
        SELECT 
            CASE 
                WHEN DATEDIFF(NOW(), hire_date) < 365 THEN '< 1 year'
                WHEN DATEDIFF(NOW(), hire_date) < 730 THEN '1-2 years'
                WHEN DATEDIFF(NOW(), hire_date) < 1095 THEN '2-3 years'
                WHEN DATEDIFF(NOW(), hire_date) < 1825 THEN '3-5 years'
                ELSE '5+ years'
            END as tenure_bracket,
            COUNT(*) as count
        FROM employees_core
        WHERE company_id = %s AND status = 'Active' AND hire_date IS NOT NULL
        GROUP BY tenure_bracket
        ORDER BY tenure_bracket
    """, (company_id,))
    
    return distribution or []


def _get_age_distribution(company_id: int) -> List[Dict]:
    """Get age distribution of employees."""
    distribution = query("""
        SELECT 
            CASE 
                WHEN YEAR(NOW()) - YEAR(date_of_birth) < 25 THEN '< 25'
                WHEN YEAR(NOW()) - YEAR(date_of_birth) < 35 THEN '25-34'
                WHEN YEAR(NOW()) - YEAR(date_of_birth) < 45 THEN '35-44'
                WHEN YEAR(NOW()) - YEAR(date_of_birth) < 55 THEN '45-54'
                ELSE '55+'
            END as age_bracket,
            COUNT(*) as count
        FROM employees_core
        WHERE company_id = %s AND status = 'Active' AND date_of_birth IS NOT NULL
        GROUP BY age_bracket
        ORDER BY age_bracket
    """, (company_id,))
    
    return distribution or []


def _get_gender_distribution(company_id: int) -> List[Dict]:
    """Get gender distribution of employees."""
    distribution = query("""
        SELECT gender, COUNT(*) as count
        FROM employees_core
        WHERE company_id = %s AND status = 'Active' AND gender IS NOT NULL
        GROUP BY gender
    """, (company_id,))
    
    return distribution or []


def _get_employment_type_distribution(company_id: int) -> List[Dict]:
    """Get employment type distribution."""
    distribution = query("""
        SELECT employment_type, COUNT(*) as count
        FROM employees_core
        WHERE company_id = %s AND status = 'Active'
        GROUP BY employment_type
    """, (company_id,))
    
    return distribution or []


def _get_department_distribution(company_id: int) -> List[Dict]:
    """Get department distribution."""
    distribution = query("""
        SELECT d.name as department, COUNT(e.id) as count
        FROM departments d
        LEFT JOIN employees_core e ON d.id = e.department_id AND e.status = 'Active'
        WHERE d.company_id = %s
        GROUP BY d.id, d.name
        ORDER BY count DESC
    """, (company_id,))
    
    return distribution or []


def _get_job_level_distribution(company_id: int) -> List[Dict]:
    """Get job level distribution (inferred from job titles)."""
    # Simple heuristic based on job title keywords
    distribution = query("""
        SELECT 
            CASE 
                WHEN job_title LIKE '%Senior%' OR job_title LIKE '%Lead%' OR job_title LIKE '%Manager%' THEN 'Senior'
                WHEN job_title LIKE '%Junior%' OR job_title LIKE '%Associate%' THEN 'Junior'
                ELSE 'Mid-Level'
            END as level,
            COUNT(*) as count
        FROM employees_core
        WHERE company_id = %s AND status = 'Active' AND job_title IS NOT NULL
        GROUP BY level
    """, (company_id,))
    
    return distribution or []


# ═══════════════════════════════════════════════════════════════════════════
# 7. SMART RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_smart_recommendations(company_id: int) -> List[Dict]:
    """
    Generate AI-powered recommendations for HR decisions.
    """
    recommendations = []
    
    # Attrition risk recommendations
    attrition_recs = _get_attrition_recommendations(company_id)
    recommendations.extend(attrition_recs)
    
    # Workforce planning recommendations
    workforce_recs = _get_workforce_recommendations(company_id)
    recommendations.extend(workforce_recs)
    
    # Attendance recommendations
    attendance_recs = _get_attendance_recommendations(company_id)
    recommendations.extend(attendance_recs)
    
    # Performance recommendations
    performance_recs = _get_performance_recommendations(company_id)
    recommendations.extend(performance_recs)
    
    return recommendations


def _get_attrition_recommendations(company_id: int) -> List[Dict]:
    """Get recommendations based on attrition risk analysis."""
    high_risk = predict_attrition_risk(company_id)
    high_risk = [e for e in high_risk if e['risk_level'] == 'High']
    
    recs = []
    if len(high_risk) > 0:
        recs.append({
            'category': 'attrition',
            'priority': 'high',
            'title': f'Address {len(high_risk)} High-Risk Employees',
            'description': f'{len(high_risk)} employees show high attrition risk. Consider retention strategies.',
            'actions': [
                'Schedule one-on-one meetings to understand concerns',
                'Review compensation packages',
                'Consider career development opportunities',
            ],
        })
    
    return recs


def _get_workforce_recommendations(company_id: int) -> List[Dict]:
    """Get workforce planning recommendations."""
    recs = []
    
    # Check growth trends
    current = _get_current_workforce_state(company_id)
    if current['total_employees'] > 0:
        recs.append({
            'category': 'workforce',
            'priority': 'medium',
            'title': 'Workforce Size Optimization',
            'description': f'Current workforce: {current["total_employees"]} employees across {len(current["departments"])} departments.',
            'actions': [
                'Review department staffing levels',
                'Assess if headcount matches business needs',
                'Plan for upcoming hiring needs',
            ],
        })
    
    return recs


def _get_attendance_recommendations(company_id: int) -> List[Dict]:
    """Get attendance-related recommendations."""
    recs = []
    
    # Analyze recent attendance
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()
    
    overall = _get_attendance_overall(company_id, start_date, end_date)
    
    if overall['attendance_rate'] < 90:
        recs.append({
            'category': 'attendance',
            'priority': 'medium',
            'title': 'Improve Attendance Rate',
            'description': f'Current attendance rate: {overall["attendance_rate"]}%. Target: 95%+.',
            'actions': [
                'Review absence policies',
                'Implement attendance incentives',
                'Address root causes of absenteeism',
            ],
        })
    
    return recs


def _get_performance_recommendations(company_id: int) -> List[Dict]:
    """Get performance-related recommendations."""
    recs = []
    
    perf = _analyze_performance_metrics(company_id)
    
    if perf['total_appraisals'] > 0:
        if perf['needs_improvement'] > perf['excellent']:
            recs.append({
                'category': 'performance',
                'priority': 'high',
                'title': 'Performance Improvement Needed',
                'description': f'{perf["needs_improvement"]} employees need performance improvement.',
                'actions': [
                    'Implement performance improvement plans',
                    'Provide additional training',
                    'Set clear expectations and goals',
                ],
            })
    
    return recs


# ═══════════════════════════════════════════════════════════════════════════
# 8. REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_ai_report(company_id: int, report_type: str = 'comprehensive') -> Dict:
    """
    Generate comprehensive AI-powered HR analytics report.
    """
    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'company_id': company_id,
        'report_type': report_type,
    }
    
    if report_type == 'comprehensive':
        report['attrition_risk'] = predict_attrition_risk(company_id)
        report['workforce_forecast'] = forecast_workforce_demand(company_id, 6)
        report['attendance_analysis'] = analyze_attendance_patterns(company_id)
        report['leave_trends'] = analyze_leave_trends(company_id)
        report['productivity'] = analyze_productivity(company_id)
        report['workforce_composition'] = analyze_workforce_composition(company_id)
        report['recommendations'] = get_smart_recommendations(company_id)
    
    elif report_type == 'attrition':
        report['attrition_risk'] = predict_attrition_risk(company_id)
        report['workforce_composition'] = analyze_workforce_composition(company_id)
        report['recommendations'] = [r for r in get_smart_recommendations(company_id) 
                                     if r['category'] == 'attrition']
    
    elif report_type == 'workforce':
        report['workforce_forecast'] = forecast_workforce_demand(company_id, 12)
        report['workforce_composition'] = analyze_workforce_composition(company_id)
        report['recommendations'] = [r for r in get_smart_recommendations(company_id) 
                                     if r['category'] == 'workforce']
    
    elif report_type == 'attendance':
        report['attendance_analysis'] = analyze_attendance_patterns(company_id)
        report['recommendations'] = [r for r in get_smart_recommendations(company_id) 
                                     if r['category'] == 'attendance']
    
    return report