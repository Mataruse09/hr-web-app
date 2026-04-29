"""
AI Analytics Routes - ML-powered workforce insights and predictions
=====================================================================
These routes provide AI/ML-powered analytics and forecasting endpoints.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime, date, timedelta
from functools import lru_cache
import hashlib
import json
import signal
import threading

from utils import login_required, roles_required
from models.db import query, mutate
from services.ai_ml_service import (
    predict_attrition_risk,
    forecast_workforce_demand,
    analyze_attendance_patterns,
    analyze_leave_trends,
    analyze_productivity,
    analyze_workforce_composition,
    get_smart_recommendations,
    generate_ai_report,
)
from services.subscription_service import ai_feature_required

logger = logging.getLogger(__name__)

ai_analytics_bp = Blueprint('ai_analytics', __name__)

# Timeout handler for AI operations
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("AI operation timed out")

# Cache for partial results
_ai_partial_cache = {}

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY CACHE FOR AI ANALYTICS (Simple TTL-based cache)
# ═══════════════════════════════════════════════════════════════════════════

class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl=300):  # 5 minutes default TTL
        self._cache = {}
        self._ttl = default_ttl
    
    def _make_key(self, company_id, *args, **kwargs):
        """Create a unique cache key."""
        key_data = f"{company_id}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key):
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now().timestamp() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with TTL."""
        ttl = ttl or self._ttl
        expiry = datetime.now().timestamp() + ttl
        self._cache[key] = (value, expiry)
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

# Global cache instance
ai_cache = SimpleCache(default_ttl=300)  # 5 minutes cache


def get_cached_ai_data(company_id, func, *args, ttl=300, **kwargs):
    """
    Get data from cache or compute and cache it.
    This won't disturb calculations - it just caches results.
    """
    cache_key = ai_cache._make_key(company_id, *args, **kwargs)
    cached = ai_cache.get(cache_key)
    
    if cached is not None:
        logger.info(f"Cache HIT for {func.__name__} (company_id={company_id})")
        return cached
    
    logger.info(f"Cache MISS for {func.__name__} (company_id={company_id})")
    result = func(company_id, *args, **kwargs)
    ai_cache.set(cache_key, result, ttl)
    return result


def _run_with_timeout(func, args, timeout_seconds=30):
    """
    Run a function with a timeout limit.
    Returns (result, None) on success or (None, error_message) on timeout.
    """
    result = [None]
    error = [None]
    
    def worker():
        try:
            result[0] = func(*args)
        except Exception as e:
            error[0] = str(e)
            logger.exception(e)
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        logger.warning(f"Function {func.__name__} timed out after {timeout_seconds}s")
        return None, f"Operation timed out after {timeout_seconds} seconds"
    
    if error[0]:
        return None, error[0]
    
    return result[0], None


def _get_ai_report_with_timeout(company_id, report_type='comprehensive', timeout=45):
    """
    Get AI report with timeout handling for slow databases.
    Falls back to cached or partial data if full report takes too long.
    """
    cache_key = f"ai_report_{company_id}_{report_type}"
    
    # Check cache first
    cached = ai_cache.get(cache_key)
    if cached is not None:
        logger.info(f"Using cached AI report for company {company_id}")
        return cached
    
    # Try to generate report with timeout
    logger.info(f"Generating AI report for company {company_id} (timeout={timeout}s)")
    result, error = _run_with_timeout(
        generate_ai_report, 
        (company_id, report_type),
        timeout
    )
    
    if error:
        logger.warning(f"AI report generation failed: {error}")
        # Return empty report structure instead of failing
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'company_id': company_id,
            'report_type': report_type,
            'error': error,
            'attrition_risk': [],
            'workforce_forecast': {'forecasts': []},
            'attendance_analysis': {'overall': {'attendance_rate': 0}},
            'leave_trends': [],
            'productivity': {'performance': {}},
            'workforce_composition': {},
            'recommendations': []
        }
    
    # Cache successful result for 5 minutes
    if result:
        ai_cache.set(cache_key, result, 300)
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# MAIN AI ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def dashboard():
    """AI Analytics Dashboard - comprehensive workforce insights."""
    company_id = session['company_id']
    
    try:
        # Get comprehensive report with timeout handling
        report = _get_ai_report_with_timeout(company_id, 'comprehensive')
        
        # Get summary stats
        summary = _get_ai_summary(report)
        
        return render_template(
            'ai_analytics/dashboard.html',
            report=report,
            summary=summary,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading AI analytics.', 'danger')
        return redirect(url_for('dashboard.index'))


def _get_ai_summary(report: dict) -> dict:
    """Extract summary statistics from AI report."""
    summary = {
        'high_risk_employees': 0,
        'avg_attrition_risk': 0,
        'projected_growth': 0,
        'attendance_rate': 0,
        'recommendations_count': 0,
    }
    
    if 'attrition_risk' in report and report['attrition_risk']:
        risks = report['attrition_risk']
        summary['high_risk_employees'] = sum(1 for r in risks if r.get('risk_level') == 'High')
        if risks:
            summary['avg_attrition_risk'] = sum(r.get('risk_score', 0) for r in risks) / len(risks)
    
    if 'workforce_forecast' in report and report['workforce_forecast']:
        forecast = report['workforce_forecast']
        if forecast.get('forecasts'):
            first_month = forecast['forecasts'][0]
            summary['projected_growth'] = first_month.get('hiring_needed', 0)
    
    if 'attendance_analysis' in report and report['attendance_analysis']:
        summary['attendance_rate'] = report['attendance_analysis'].get('overall', {}).get('attendance_rate', 0)
    
    if 'recommendations' in report:
        summary['recommendations_count'] = len(report['recommendations'])
    
    return summary


# ═══════════════════════════════════════════════════════════════════════════
# ATTRITION RISK PREDICTION
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/attrition-risk')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def attrition_risk():
    """View attrition risk predictions."""
    company_id = session['company_id']
    employee_id = request.args.get('employee_id', type=int)
    
    try:
        # Cache for 5 minutes (attrition risk doesn't change frequently)
        if employee_id:
            risks = get_cached_ai_data(company_id, predict_attrition_risk, employee_id, ttl=300)
        else:
            risks = get_cached_ai_data(company_id, predict_attrition_risk, ttl=300)
        
        # Get employee details for display
        if employee_id:
            emp = query("""
                SELECT e.id, e.first_name, e.last_name, e.job_title, d.name as department
                FROM employees_core e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.id = %s AND e.company_id = %s
            """, (employee_id, company_id), one=True)
            
            if emp and risks:
                risks[0]['employee_name'] = f"{emp['first_name']} {emp['last_name']}"
                risks[0]['job_title'] = emp['job_title']
                risks[0]['department'] = emp['department']
        
        return render_template(
            'ai_analytics/attrition_risk.html',
            risks=risks,
            selected_employee_id=employee_id,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error analyzing attrition risk.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/attrition-risk')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def api_attrition_risk():
    """API endpoint for attrition risk data."""
    company_id = session['company_id']
    employee_id = request.args.get('employee_id', type=int)
    
    try:
        # Cache for 5 minutes
        if employee_id:
            risks = get_cached_ai_data(company_id, predict_attrition_risk, employee_id, ttl=300)
        else:
            risks = get_cached_ai_data(company_id, predict_attrition_risk, ttl=300)
        
        return jsonify({
            'success': True,
            'data': risks,
            'count': len(risks),
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# WORKFORCE DEMAND FORECASTING
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/forecast')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def workforce_forecast():
    """View AI-powered workforce demand forecasts."""
    company_id = session['company_id']
    months = request.args.get('months', type=int, default=12)
    
    try:
        # Cache forecast for 10 minutes (forecasts change less frequently)
        forecast = get_cached_ai_data(company_id, forecast_workforce_demand, months, ttl=600)
        
        return render_template(
            'ai_analytics/forecast.html',
            forecast=forecast,
            months=months,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error generating forecast.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/forecast')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def api_forecast():
    """API endpoint for workforce forecast data."""
    company_id = session['company_id']
    months = request.args.get('months', type=int, default=12)
    
    try:
        # Cache for 10 minutes
        forecast = get_cached_ai_data(company_id, forecast_workforce_demand, months, ttl=600)
        return jsonify({
            'success': True,
            'data': forecast,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# ATTENDANCE PATTERN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/attendance')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def attendance_analysis():
    """View AI-powered attendance pattern analysis."""
    company_id = session['company_id']
    days = request.args.get('days', type=int, default=90)
    
    try:
        # Cache for 5 minutes
        analysis = get_cached_ai_data(company_id, analyze_attendance_patterns, days, ttl=300)
        
        return render_template(
            'ai_analytics/attendance.html',
            analysis=analysis,
            days=days,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error analyzing attendance patterns.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/attendance')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def api_attendance():
    """API endpoint for attendance analysis data."""
    company_id = session['company_id']
    days = request.args.get('days', type=int, default=90)
    
    try:
        # Cache for 5 minutes
        analysis = get_cached_ai_data(company_id, analyze_attendance_patterns, days, ttl=300)
        return jsonify({
            'success': True,
            'data': analysis,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# LEAVE TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/leave')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def leave_analysis():
    """View AI-powered leave trend analysis."""
    company_id = session['company_id']
    year = request.args.get('year', type=int, default=date.today().year)
    
    try:
        # Cache for 10 minutes (leave trends are monthly)
        analysis = get_cached_ai_data(company_id, analyze_leave_trends, year, ttl=600)
        
        return render_template(
            'ai_analytics/leave.html',
            analysis=analysis,
            year=year,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error analyzing leave trends.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/leave')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def api_leave():
    """API endpoint for leave trend data."""
    company_id = session['company_id']
    year = request.args.get('year', type=int, default=date.today().year)
    
    try:
        # Cache for 10 minutes
        analysis = get_cached_ai_data(company_id, analyze_leave_trends, year, ttl=600)
        return jsonify({
            'success': True,
            'data': analysis,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTIVITY INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/productivity')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def productivity_insights():
    """View AI-powered productivity insights."""
    company_id = session['company_id']
    
    try:
        # Cache for 5 minutes
        analysis = get_cached_ai_data(company_id, analyze_productivity, ttl=300)
        
        # Ensure analysis is a dict (handle case where cache returns wrong type)
        if not isinstance(analysis, dict):
            logger.warning(f"Invalid analysis type: {type(analysis)}, re-computing")
            analysis = analyze_productivity(company_id)
        
        return render_template(
            'ai_analytics/productivity.html',
            analysis=analysis,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error analyzing productivity.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/productivity')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def api_productivity():
    """API endpoint for productivity data."""
    company_id = session['company_id']
    
    try:
        # Cache for 5 minutes
        analysis = get_cached_ai_data(company_id, analyze_productivity, ttl=300)
        return jsonify({
            'success': True,
            'data': analysis,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# WORKFORCE COMPOSITION
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/composition')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def workforce_composition():
    """View workforce composition and diversity analysis."""
    company_id = session['company_id']
    
    try:
        # Cache for 10 minutes (composition changes slowly)
        analysis = get_cached_ai_data(company_id, analyze_workforce_composition, ttl=600)
        
        return render_template(
            'ai_analytics/composition.html',
            analysis=analysis,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error analyzing workforce composition.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/composition')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def api_composition():
    """API endpoint for workforce composition data."""
    company_id = session['company_id']
    
    try:
        # Cache for 10 minutes
        analysis = get_cached_ai_data(company_id, analyze_workforce_composition, ttl=600)
        return jsonify({
            'success': True,
            'data': analysis,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# SMART RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/recommendations')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def recommendations():
    """View AI-powered smart recommendations."""
    company_id = session['company_id']
    
    try:
        # Cache for 5 minutes
        recs = get_cached_ai_data(company_id, get_smart_recommendations, ttl=300)
        
        # Filter to only include dict objects (defensive against string entries)
        valid_recs = [r for r in recs if isinstance(r, dict)]
        
        # Group by priority
        high_priority = [r for r in valid_recs if r.get('priority') == 'high']
        medium_priority = [r for r in valid_recs if r.get('priority') == 'medium']
        low_priority = [r for r in valid_recs if r.get('priority') == 'low']
        
        return render_template(
            'ai_analytics/recommendations.html',
            recommendations=valid_recs,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error generating recommendations.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/recommendations')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def api_recommendations():
    """API endpoint for recommendations data."""
    company_id = session['company_id']
    
    try:
        # Cache for 5 minutes
        recs = get_cached_ai_data(company_id, get_smart_recommendations, ttl=300)
        return jsonify({
            'success': True,
            'data': recs,
            'count': len(recs),
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE REPORT
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/ai-analytics/report')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def full_report():
    """Generate and view comprehensive AI analytics report."""
    company_id = session['company_id']
    report_type = request.args.get('type', 'comprehensive')
    
    try:
        # Cache for 10 minutes
        report = get_cached_ai_data(company_id, generate_ai_report, report_type, ttl=600)
        
        return render_template(
            'ai_analytics/report.html',
            report=report,
            report_type=report_type,
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error generating report.', 'danger')
        return redirect(url_for('ai_analytics.dashboard'))


@ai_analytics_bp.route('/api/ai/report')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
@ai_feature_required
def api_report():
    """API endpoint for comprehensive report data."""
    company_id = session['company_id']
    report_type = request.args.get('type', 'comprehensive')
    
    try:
        # Cache for 10 minutes
        report = get_cached_ai_data(company_id, generate_ai_report, report_type, ttl=600)
        return jsonify({
            'success': True,
            'data': report,
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════════
# QUICK KPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@ai_analytics_bp.route('/api/ai/quick-stats')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
@ai_feature_required
def api_quick_stats():
    """Quick stats API for dashboard widgets."""
    company_id = session['company_id']
    
    try:
        # Cache for 3 minutes (quick stats need to be fresher)
        # Get key stats quickly
        risks = get_cached_ai_data(company_id, predict_attrition_risk, ttl=180)
        high_risk_count = sum(1 for r in risks if r.get('risk_level') == 'High')
        
        forecast = get_cached_ai_data(company_id, forecast_workforce_demand, 3, ttl=180)
        next_month_forecast = forecast.get('forecasts', [{}])[0] if forecast.get('forecasts') else {}
        
        attendance = get_cached_ai_data(company_id, analyze_attendance_patterns, 30, ttl=180)
        
        return jsonify({
            'success': True,
            'data': {
                'high_risk_employees': high_risk_count,
                'projected_hiring': next_month_forecast.get('hiring_needed', 0),
                'attendance_rate': attendance.get('overall', {}).get('attendance_rate', 0),
                'total_employees': len(risks),
            },
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'success': False, 'error': str(e)}), 500