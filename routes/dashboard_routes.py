from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from utils import login_required, roles_required
from services.calculation_services import get_dashboard_kpis, get_personal_kpis, get_monthly_attrition_data, get_kpi_cache
from models import employee_model
import logging
import traceback

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


def render_dashboard(role, company_id):
    from models.company_model import get_by_id
    
    # Get company with error handling
    try:
        company = get_by_id(company_id)
    except Exception as e:
        logger.error(f"Error getting company: {e}")
        company = None
    
    # Get KPIs with error handling
    try:
        kpis = get_dashboard_kpis(company_id)
    except Exception as e:
        logger.error(f"Error getting dashboard KPIs: {e}")
        logger.error(traceback.format_exc())
        # Return default KPIs to prevent empty dashboard
        kpis = {
            'total_employees': 0,
            'active_employees': 0,
            'on_leave': 0,
            'new_hires': 0,
            'attrition_rate': 0,
            'attendance_rate': 0,
            'pending_leaves': 0,
            'total_departments': 0,
        }
    
    # Get departments with error handling
    try:
        departments = employee_model.get_departments(company_id)
    except Exception as e:
        logger.error(f"Error getting departments: {e}")
        departments = []
    
    return render_template(
        'dashboard.html',
        role=role,
        company=company,
        kpis=kpis,
        departments=departments,
        is_personal=False
    )


@dashboard_bp.route('/')
def index():
    """Public landing page - accessible without login for Google indexing"""
    # If user is logged in, redirect to their dashboard
    if session.get('user_id'):
        return redirect(url_for('dashboard.index_authenticated'))
    
    # Public landing page for unauthenticated users (Google indexing)
    return render_template('landing.html')


@dashboard_bp.route('/dashboard')
@login_required
def index_authenticated():
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    role = (session.get('role') or 'Employee').strip()

    # If role is not set or invalid, try to get from user_roles table
    if not role or role not in ['Admin', 'HR', 'CHRO', 'Manager', 'Employee', 'company_admin']:
        from models import user_model as um
        user_roles = um.get_user_roles(user_id, company_id)
        if user_roles and len(user_roles) > 0:
            role = user_roles[0]['role']
            session['role'] = role

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    if role in ('Admin', 'company_admin'):
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'HR':
        return redirect(url_for('dashboard.hr_dashboard'))
    elif role == 'CHRO':
        return redirect(url_for('dashboard.chro_analytics'))
    elif role == 'Manager':
        return redirect(url_for('dashboard.manager_dashboard'))
    elif role == 'Employee':
        return redirect(url_for('dashboard.employee_dashboard'))

    return render_dashboard(role, company_id)


@dashboard_bp.route('/dashboard/employee')
@login_required
@roles_required('Employee')
def employee_dashboard():
    """Personal employee dashboard - shows only their own data"""
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    # Get the employee's own record
    employee = employee_model.get_by_user_id(user_id, company_id)
    
    if not employee:
        flash('Profile not linked to employee.', 'warning')
        return redirect(url_for('auth.login'))

    # Get personal KPIs
    personal_kpis = get_personal_kpis(company_id, employee['id'])

    from models.company_model import get_by_id
    company = get_by_id(company_id)

    return render_template(
        'dashboard.html',
        role='Employee',
        company=company,
        kpis=personal_kpis,
        employee=employee,
        is_personal=True
    )


@dashboard_bp.route('/dashboard/admin')
@login_required
@roles_required('Admin', 'company_admin')
def admin_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    from models.company_model import get_by_id
    company = get_by_id(company_id)
    
    # Get KPIs with caching enabled for better performance
    kpis = get_dashboard_kpis(company_id, use_cache=True)
    departments = employee_model.get_departments(company_id)

    return render_template(
        'dashboard.html',
        company=company,
        kpis=kpis,
        departments=departments,
        role='Admin',
        is_personal=False
    )


@dashboard_bp.route('/dashboard/hr')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def hr_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    from models.company_model import get_by_id
    company = get_by_id(company_id)
    kpis = get_dashboard_kpis(company_id, use_cache=True)
    departments = employee_model.get_departments(company_id)

    return render_template(
        'dashboard.html',
        company=company,
        kpis=kpis,
        departments=departments,
        role='HR',
        is_personal=False
    )


@dashboard_bp.route('/dashboard/manager')
@login_required
@roles_required('Manager', 'Admin')
def manager_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    from models.company_model import get_by_id
    company = get_by_id(company_id)
    kpis = get_dashboard_kpis(company_id, use_cache=True)
    departments = employee_model.get_departments(company_id)

    return render_template(
        'dashboard.html',
        company=company,
        kpis=kpis,
        departments=departments,
        role='Manager',
        is_personal=False
    )


@dashboard_bp.route('/dashboard/chro')
@login_required
@roles_required('CHRO', 'Admin')
def chro_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    return render_dashboard('CHRO', company_id)


@dashboard_bp.route('/dashboard/chro/analytics')
@login_required
@roles_required('CHRO')
def chro_analytics():
    import logging
    logger = logging.getLogger(__name__)
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    try:
        from models.company_model import get_by_id
        from services.ai_ml_service import (
            forecast_workforce_demand,
            predict_attrition_risk,
            get_smart_recommendations,
        )
        
        company = get_by_id(company_id)
        kpis = get_dashboard_kpis(company_id)
        employees = employee_model.get_all(company_id)

        attrition = kpis.get('attrition_rate', 0)
        
        # Get real monthly attrition data for the chart
        monthly_attrition = get_monthly_attrition_data(company_id, 6)
        
        # Get AI analytics data
        ai_forecast = forecast_workforce_demand(company_id, 6)
        ai_attrition = predict_attrition_risk(company_id)
        ai_recommendations = get_smart_recommendations(company_id)
        
        # Calculate AI summary stats
        high_risk_count = sum(1 for r in ai_attrition if r.get('risk_level') == 'High') if ai_attrition else 0
        avg_risk = sum(r.get('risk_score', 0) for r in ai_attrition) / len(ai_attrition) if ai_attrition else 0
        
        projected_hiring = 0
        if ai_forecast and ai_forecast.get('forecasts'):
            for f in ai_forecast['forecasts']:
                projected_hiring += f.get('hiring_needed', 0)
        
        ai_summary = {
            'projected_hiring': projected_hiring,
            'high_risk_employees': high_risk_count,
            'avg_attrition_risk': round(avg_risk, 1),
            'recommendations_count': len(ai_recommendations),
        }

        return render_template(
            'dashboard_chro_analytics.html',
            company=company,
            kpis=kpis,
            attrition=attrition,
            employees=len(employees),
            monthly_attrition=monthly_attrition,
            ai_forecast=ai_forecast,
            ai_attrition=ai_attrition,
            ai_recommendations=ai_recommendations,
            ai_summary=ai_summary,
        )
    except Exception as e:
        logger.error(f"Error in chro_analytics: {e}", exc_info=True)
        flash(f"Error loading CHRO analytics: {str(e)}", "danger")
        return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/dashboard/admin/setup')
@login_required
@roles_required('Admin', 'company_admin')
def admin_setup():
    role = session.get('role')

    if role not in ['Admin', 'company_admin']:
        flash('Access denied — only company admins can do setup.', 'danger')
        return redirect(url_for('dashboard.index'))

    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    from models.company_model import get_by_id
    company = get_by_id(company_id)

    # Get KPIs for the dashboard
    kpis = get_dashboard_kpis(company_id)

    return render_template(
        'dashboard_admin_setup.html',
        company=company,
        kpis=kpis
    )


@dashboard_bp.route('/dashboard/billing')
@login_required
@roles_required('Admin', 'company_admin')
def billing():
    """Billing dashboard - shows subscription and billing info"""
    role = session.get('role')

    if role not in ['Admin', 'company_admin']:
        flash('Access denied — only company admins can access billing.', 'danger')
        return redirect(url_for('dashboard.index'))

    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    from models.company_model import get_by_id
    from models.subscription_model import get_company_subscription
    from services.subscription_service import get_available_features
    
    company = get_by_id(company_id)
    subscription = get_company_subscription(company_id)
    available_features = get_available_features(company_id)

    # Get KPIs for the billing dashboard
    kpis = get_dashboard_kpis(company_id)

    return render_template(
        'dashboard_billing.html',
        company=company,
        subscription=subscription,
        available_features=available_features,
        kpis=kpis
    )