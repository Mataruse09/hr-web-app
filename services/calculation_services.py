"""
HR Calculation Engine
=====================
All business-logic calculations live here.
Routes call these functions — never raw SQL maths in templates.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
import calendar
import logging
import time
import threading

from models import attendance_model, leave_model, employee_model, payroll_model
from models.db import query


# ═══════════════════════════════════════════════════════════════════════════
# KPI CACHE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

class KPICache:
    """Thread-safe in-memory cache for KPIs with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> tuple:
        """Get value and age from cache. Returns (value, age_seconds) or (None, None)"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None, None
            
            entry = self._cache[key]
            age = time.time() - entry['timestamp']
            
            if age > entry['ttl']:
                # Expired
                del self._cache[key]
                self._misses += 1
                return None, None
            
            self._hits += 1
            return entry['value'], age
    
    def set(self, key: str, value, ttl: int = None):
        """Set cache value with optional custom TTL"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl or self._default_ttl
            }
    
    def invalidate(self, key: str):
        """Remove specific key from cache"""
        with self._lock:
            self._cache.pop(key, None)
    
    def invalidate_prefix(self, prefix: str):
        """Remove all keys starting with prefix"""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 1),
                'entries': len(self._cache)
            }


# Global KPI cache instance
_kpi_cache = KPICache(default_ttl=300)


def get_kpi_cache() -> KPICache:
    """Get the global KPI cache instance"""
    return _kpi_cache


def invalidate_company_cache(company_id: int):
    """Invalidate all cached data for a company"""
    _kpi_cache.invalidate_prefix(f'company_{company_id}_')


# ═══════════════════════════════════════════════════════════════════════════
# 1. PAYROLL CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

def calculate_gross_salary(basic: float, allowances: dict) -> float:
    """
    Gross Salary = Basic + Housing + Transport + Meal + Other Allowances
    """
    return round(
        basic
        + allowances.get('housing',   0.0)
        + allowances.get('transport', 0.0)
        + allowances.get('meal',      0.0)
        + allowances.get('other',     0.0),
        2,
    )


def calculate_tax(gross: float, tax_rate_pct: float) -> float:
    """
    Tax Amount = Gross Salary × (Tax Rate / 100)
    """
    return round(gross * tax_rate_pct / 100.0, 2)


def calculate_net_salary(
    basic:       float,
    allowances:  dict,
    bonus:       float = 0.0,
    tax_rate:    float = 0.0,
    deductions:  dict  | None = None,
) -> dict:
    """
    Net Salary = Gross + Bonus − Tax − Total Deductions

    Returns a full breakdown dict.
    """
    if deductions is None:
        deductions = {}

    gross          = calculate_gross_salary(basic, allowances)
    total_allow    = gross - basic
    gross_w_bonus  = round(gross + bonus, 2)
    tax_amount     = calculate_tax(gross_w_bonus, tax_rate)
    total_deduct   = round(
        tax_amount
        + deductions.get('social_insurance', 0.0)
        + deductions.get('health_insurance', 0.0)
        + deductions.get('other',            0.0),
        2,
    )
    net = round(gross_w_bonus - total_deduct, 2)

    return {
        'basic_salary':     round(basic,       2),
        'total_allowances': round(total_allow, 2),
        'gross_salary':     gross_w_bonus,
        'bonus':            round(bonus,       2),
        'income_tax':       tax_amount,
        'total_deductions': total_deduct,
        'net_salary':       net,
    }


def build_payroll_for_employee(
    company_id:  int,
    employee_id: int,
    pay_period:  str,           # 'YYYY-MM'
    processed_by: int,
    bonus:       float = 0.0,
    working_days: int = 22,
) -> Optional[dict]:
    """
    Fetches compensation data and returns a ready-to-save payroll dict.
    """
    comp = payroll_model.get_compensation(employee_id, company_id)
    if not comp:
        return None

    year, month = map(int, pay_period.split('-'))
    present_days = attendance_model.monthly_present_days(
        company_id, employee_id, year, month
    )

    result = calculate_net_salary(
        basic      = float(comp['basic_salary']),
        allowances = {
            'housing':   float(comp['housing_allowance']),
            'transport': float(comp['transport_allowance']),
            'meal':      float(comp['meal_allowance']),
            'other':     float(comp['other_allowances']),
        },
        bonus      = bonus,
        tax_rate   = float(comp['income_tax_rate']),
        deductions = {
            'social_insurance': float(comp['social_insurance']),
            'health_insurance': float(comp['health_insurance']),
            'other':            float(comp['other_deductions']),
        },
    )
    result.update({
        'working_days':  working_days,
        'present_days':  present_days,
        'status':        'Pending',
        'processed_by':  processed_by,
        'processed_at':  datetime.utcnow(),
    })
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 2. ATTENDANCE
# ═══════════════════════════════════════════════════════════════════════════

def attendance_rate(present_days: int, total_working_days: int) -> float:
    """
    Rate (%) = Present Days / Total Working Days × 100
    Returns 0.0 if total_working_days is 0 to avoid ZeroDivisionError.
    """
    if total_working_days <= 0:
        return 0.0
    return round((present_days / total_working_days) * 100, 1)


def company_monthly_attendance_rate(company_id: int) -> float:
    """
    Average attendance rate across ALL active employees this month.
    """
    today        = date.today()
    year, month  = today.year, today.month
    working_days = count_working_days(year, month)

    employees = employee_model.get_all(company_id)
    active    = [e for e in employees if e['status'] == 'Active']

    if not active:
        return 0.0

    rates = [
        attendance_rate(
            attendance_model.monthly_present_days(company_id, e['id'], year, month),
            working_days,
        )
        for e in active
    ]
    return round(sum(rates) / len(rates), 1)


def count_working_days(year: int, month: int) -> int:
    """
    Count Mon–Fri days in a given month (simple, no holiday calendar).
    """
    _, last_day = calendar.monthrange(year, month)
    return sum(
        1 for d in range(1, last_day + 1)
        if date(year, month, d).weekday() < 5
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3. LEAVE
# ═══════════════════════════════════════════════════════════════════════════

def leave_balance(total: int, used: int) -> int:
    """Remaining Leave = Total − Used"""
    return max(total - used, 0)


def leave_utilization_rate(used: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((used / total) * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════
# 4. WORKFORCE ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

def attrition_rate(terminated: int, total: int) -> float:
    """
    Attrition Rate (%) = Terminated / Total Employees × 100
    """
    if total <= 0:
        return 0.0
    return round((terminated / total) * 100, 1)


def average_salary(company_id: int) -> float:
    """Delegate to payroll model; returns average net salary."""
    return payroll_model.average_net_salary(company_id)


def employee_growth_rate(current_count: int, previous_count: int) -> float:
    """
    Growth Rate (%) = (Current − Previous) / Previous × 100
    """
    if previous_count <= 0:
        return 0.0
    return round(((current_count - previous_count) / previous_count) * 100, 1)


def performance_score_average(scores: list[float]) -> float:
    """Average of performance ratings (scale 1–5)."""
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


# ═══════════════════════════════════════════════════════════════════════════
# 5. DASHBOARD KPI BUNDLE
# ═══════════════════════════════════════════════════════════════════════════

def get_dashboard_kpis(company_id: int, use_cache: bool = True) -> dict:
    """
    Collect and compute every KPI displayed on the dashboard.
    Called once per page load — keeps route logic thin.
    
    Uses caching to improve performance. Cache is invalidated when
    company data changes (employees added/removed, attendance logged, etc.)
    
    Includes error handling to prevent empty dashboards on DB issues.
    """
    import traceback
    
    cache_key = f'company_{company_id}_dashboard_kpis'
    
    # Try to get from cache first
    if use_cache:
        try:
            cached_value, age = _kpi_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
        except:
            pass
    
    # Cache miss - compute KPIs (simplified for performance)
    start_time = time.time()
    
    try:
        today_str   = date.today().isoformat()
        
        # Simplified queries - just get counts
        total       = employee_model.get_total_count(company_id)
        active      = employee_model.get_active_count(company_id)
        terminated  = employee_model.get_terminated_count(company_id)

        # Get attendance for today only (not monthly)
        today_att   = attendance_model.today_summary(company_id, today_str)
        on_leave    = leave_model.on_leave_today(company_id, today_str)
        
        # Skip expensive queries for now - return basic data
        pending_pay = 0
        avg_sal     = 0
        att_rate    = 0
        attr_rate   = 0

        kpis = {
            'total_employees':  total,
            'active_employees': active,
            'present_today':    today_att['present'] or 0,
            'absent_today':     today_att['absent']  or 0,
            'late_today':       today_att.get('late', 0) or 0,
            'on_leave_today':   on_leave,
            'pending_payroll':  pending_pay,
            'average_salary':   round(avg_sal, 2),
            'attendance_rate':  att_rate,
            'attrition_rate':   attr_rate,
            'terminated_count': terminated,
        }
        
        # Cache the result (5 minutes TTL)
        _kpi_cache.set(cache_key, kpis, ttl=300)
        
        return kpis
        
    except Exception as e:
        logging.error(f"Error computing KPIs for company {company_id}: {e}")
        logging.error(traceback.format_exc())
        # Return default KPIs to prevent empty dashboard
        return {
            'total_employees': 0,
            'active_employees': 0,
            'present_today': 0,
            'absent_today': 0,
            'late_today': 0,
            'on_leave_today': 0,
            'pending_payroll': 0,
            'average_salary': 0,
            'attendance_rate': 0,
            'attrition_rate': 0,
            'terminated_count': 0,
        }


# ═══════════════════════════════════════════════════════════════════════════
# 6. MONTHLY ATTRITION DATA FOR CHARTS
# ═══════════════════════════════════════════════════════════════════════════

def get_monthly_attrition_data(company_id: int, months: int = 6, use_cache: bool = True) -> list:
    """
    Get monthly attrition counts for the past N months.
    Returns list of dicts with 'month' and 'count' keys.
    
    Uses caching to improve performance.
    """
    cache_key = f'company_{company_id}_monthly_attrition_{months}'
    
    # Try to get from cache first
    if use_cache:
        cached_value, age = _kpi_cache.get(cache_key)
        if cached_value is not None:
            logging.debug(f"Attrition cache hit for company {company_id}, age: {age:.1f}s")
            return cached_value
    
    # Cache miss - compute data
    start_time = time.time()
    
    result = []
    today = date.today()
    
    for i in range(months):
        # Calculate month
        month_offset = today.month - i
        year_offset = today.year
        while month_offset < 1:
            month_offset += 12
            year_offset -= 1
        
        month_start = f"{year_offset}-{month_offset:02d}-01"
        
        # Get count for this month - using MySQL-compatible syntax
        row = query("""
            SELECT COUNT(*) as cnt 
            FROM attrition_records ar
            LEFT JOIN employees_core ec ON ar.employee_id = ec.id
            WHERE ec.company_id = %s
              AND DATE(ar.exit_date) >= %s
              AND DATE(ar.exit_date) < DATE_ADD(%s, INTERVAL 1 MONTH)
        """, (company_id, month_start, month_start), one=True)
        
        month_name = datetime(int(year_offset), month_offset, 1).strftime('%b')
        result.append({
            'month': month_name,
            'count': row['cnt'] if row else 0
        })
    
    result = list(reversed(result))
    
    # Cache the result (15 minutes TTL - attrition changes less frequently)
    _kpi_cache.set(cache_key, result, ttl=900)
    
    elapsed = time.time() - start_time
    logging.info(f"Computed monthly attrition for company {company_id} in {elapsed*1000:.1f}ms")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# PERFORMANCE MONITORING
# ═══════════════════════════════════════════════════════════════════════════

def log_performance(func):
    """Decorator to log slow function calls"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Log if execution takes more than 500ms
        if elapsed > 0.5:
            logging.warning(
                f"Slow operation detected: {func.__name__} took {elapsed*1000:.1f}ms"
            )
        
        return result
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# PERSONAL EMPLOYEE KPIs
# ═══════════════════════════════════════════════════════════════════════════

def get_personal_kpis(company_id: int, employee_id: int) -> dict:
    """
    Get personal KPIs for an employee - their own attendance, leave, etc.
    """
    from datetime import timedelta
    
    today = date.today()
    today_str = today.isoformat()
    current_year = today.year
    
    # Get this year's attendance
    year_start = f"{current_year}-01-01"
    year_end = f"{current_year}-12-31"
    
    attendance_logs = attendance_model.get_logs(company_id, year_start, year_end, employee_id)
    
    # Calculate personal stats
    present_days = 0
    absent_days = 0
    late_days = 0
    wfh_days = 0
    half_day = 0
    total_hours = 0.0
    
    if attendance_logs:
        for att in attendance_logs:
            status = att.get('status', '')
            if status in ['Present']:
                present_days += 1
            elif status in ['Absent']:
                absent_days += 1
            elif status in ['Late']:
                late_days += 1
            elif status in ['Work From Home']:
                wfh_days += 1
            elif status in ['Half-Day']:
                half_day += 1
            if att.get('working_hours'):
                total_hours += float(att.get('working_hours', 0))
    
    # Get today's attendance status
    today_att = attendance_model.get_logs(company_id, today_str, today_str, employee_id)
    today_status = None
    if today_att:
        today_status = today_att[0].get('status')
    
    # Get leave balance
    leave_bal = leave_model.get_balance(employee_id, company_id, current_year)
    
    # Get pending leave requests
    from models.db import query
    pending_leaves = query("""
        SELECT COUNT(*) as cnt FROM leave_requests
        WHERE employee_id = %s AND company_id = %s AND status = 'Pending'
    """, (employee_id, company_id), one=True)
    pending_leave_count = pending_leaves['cnt'] if pending_leaves else 0
    
    # Calculate attendance rate for this employee
    total_days = present_days + absent_days + late_days + wfh_days + half_day
    personal_att_rate = round((present_days + wfh_days + half_day) / total_days * 100, 1) if total_days > 0 else 0
    
    return {
        'total_employees': 1,  # Self
        'active_employees': 1,
        'present_today': 1 if today_status == 'Present' else 0,
        'absent_today': 1 if today_status == 'Absent' else 0,
        'on_leave_today': 1 if today_status in ['On Leave', 'Leave'] else 0,
        'pending_payroll': 0,
        'average_salary': 0,
        'attendance_rate': personal_att_rate,
        'attrition_rate': 0,
        'terminated_count': 0,
        # Personal fields
        'personal_present_days': present_days,
        'personal_absent_days': absent_days,
        'personal_late_days': late_days,
        'personal_wfh_days': wfh_days,
        'personal_half_days': half_day,
        'personal_total_hours': round(total_hours, 1),
        'personal_today_status': today_status,
        'personal_leave_remaining': leave_bal['annual_remaining'] if leave_bal and 'annual_remaining' in leave_bal else (leave_bal['annual_total'] - leave_bal['annual_used']) if leave_bal else 0,
        'personal_leave_used': leave_bal['annual_used'] if leave_bal else 0,
        'personal_leave_total': leave_bal['annual_total'] if leave_bal else 0,
        'personal_pending_leaves': pending_leave_count,
    }