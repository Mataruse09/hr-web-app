from flask import Blueprint, render_template, session, redirect, url_for, flash
from utils import login_required, roles_required
from services.calculation_services import get_dashboard_kpis
from models import employee_model

dashboard_bp = Blueprint('dashboard', __name__)


def render_dashboard(role, company_id):
    kpis = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)
    return render_template('dashboard.html', role=role, kpis=kpis, departments=departments)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    company_id  = session['company_id']
    role        = session.get('role', 'Employee')

    if role in ('Admin', 'company_admin'):
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'HR':
        return redirect(url_for('dashboard.hr_dashboard'))
    elif role == 'CHRO':
        return redirect(url_for('dashboard.chro_dashboard'))
    elif role == 'Manager':
        return redirect(url_for('dashboard.manager_dashboard'))

    return render_dashboard(role, company_id)


@dashboard_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    company_id  = session['company_id']
    kpis        = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)
    return render_template('dashboard.html', kpis=kpis, departments=departments, role='Admin')


@dashboard_bp.route('/dashboard/hr')
@login_required
def hr_dashboard():
    company_id  = session['company_id']
    kpis        = get_dashboard_kpis(company_id)
    return render_template('dashboard.html', kpis=kpis, role='HR')


@dashboard_bp.route('/dashboard/manager')
@login_required
def manager_dashboard():
    company_id  = session['company_id']
    kpis        = get_dashboard_kpis(company_id)
    return render_template('dashboard.html', kpis=kpis, role='Manager')


@dashboard_bp.route('/dashboard/chro')
@login_required
def chro_dashboard():
    company_id  = session['company_id']
    return render_dashboard('CHRO', company_id)


@dashboard_bp.route('/dashboard/chro/analytics')
@login_required
@roles_required('CHRO')
def chro_analytics():
    company_id = session['company_id']
    kpis = get_dashboard_kpis(company_id)
    employees = employee_model.get_all(company_id)
    attrition = kpis.get('attrition_rate', 0)
    return render_template('dashboard_chro_analytics.html', kpis=kpis, attrition=attrition, employees=len(employees))


@dashboard_bp.route('/dashboard/admin/setup')
@login_required
def admin_setup():
    if session.get('role') not in ['Admin', 'company_admin']:
        flash('Access denied — only company admins can do setup.', 'danger')
        return redirect(url_for('dashboard.index'))

    company_id = session['company_id']
    from models.company_model import get_by_id
    company = get_by_id(company_id)
    return render_template('dashboard_admin_setup.html', company=company)
