from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils import login_required, roles_required
from services.calculation_services import get_dashboard_kpis, get_personal_kpis
from models import employee_model

dashboard_bp = Blueprint('dashboard', __name__)


def render_dashboard(role, company_id):
    kpis = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)
    return render_template(
        'dashboard.html',
        role=role,
        kpis=kpis,
        departments=departments
    )


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    import logging
    logger = logging.getLogger(__name__)
    
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    role = (session.get('role') or 'Employee').strip()

    logger.info(f"Dashboard index - User: {user_id}, Role from session: '{role}'")

    # If role is not set or invalid, try to get from user_roles table
    if not role or role not in ['Admin', 'HR', 'CHRO', 'Manager', 'Employee', 'company_admin']:
        from models import user_model as um
        user_roles = um.get_user_roles(user_id, company_id)
        if user_roles and len(user_roles) > 0:
            role = user_roles[0]['role']
            session['role'] = role
            logger.info(f"Role updated from user_roles table: '{role}'")

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    if role in ('Admin', 'company_admin'):
        logger.info("Redirecting to admin_dashboard")
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'HR':
        logger.info("Redirecting to hr_dashboard")
        return redirect(url_for('dashboard.hr_dashboard'))
    elif role == 'CHRO':
        logger.info("Redirecting to chro_analytics")
        return redirect(url_for('dashboard.chro_analytics'))
    elif role == 'Manager':
        logger.info("Redirecting to manager_dashboard")
        return redirect(url_for('dashboard.manager_dashboard'))
    elif role == 'Employee':
        logger.info("Redirecting to employee_dashboard")
        return redirect(url_for('dashboard.employee_dashboard'))

    logger.warning(f"Unknown role '{role}', falling back to render_dashboard")
    return render_dashboard(role, company_id)


@dashboard_bp.route('/dashboard/employee')
@login_required
@roles_required('Employee')
def employee_dashboard():
    """Personal employee dashboard - shows only their own data"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Accessing employee_dashboard")
    
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    user_role = session.get('role')
    logger.info(f"Employee dashboard - user_role: {user_role}, user_id: {user_id}")

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

    return render_template(
        'dashboard.html',
        role='Employee',
        kpis=personal_kpis,
        employee=employee,
        is_personal=True
    )


@dashboard_bp.route('/dashboard/admin')
@login_required
@roles_required('Admin', 'company_admin')
def admin_dashboard():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Accessing admin_dashboard")
    
    company_id = session.get('company_id')
    user_role = session.get('role')
    logger.info(f"Admin dashboard - user_role: {user_role}")

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    kpis = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)

    return render_template(
        'dashboard.html',
        kpis=kpis,
        departments=departments,
        role='Admin'
    )


@dashboard_bp.route('/dashboard/hr')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def hr_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    kpis = get_dashboard_kpis(company_id)

    return render_template(
        'dashboard.html',
        kpis=kpis,
        role='HR'
    )


@dashboard_bp.route('/dashboard/manager')
@login_required
@roles_required('Manager', 'Admin')
def manager_dashboard():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    kpis = get_dashboard_kpis(company_id)

    return render_template(
        'dashboard.html',
        kpis=kpis,
        role='Manager'
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
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    kpis = get_dashboard_kpis(company_id)
    employees = employee_model.get_all(company_id)

    attrition = kpis.get('attrition_rate', 0)

    return render_template(
        'dashboard_chro_analytics.html',
        kpis=kpis,
        attrition=attrition,
        employees=len(employees)
    )


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

    return render_template(
        'dashboard_admin_setup.html',
        company=company
    )