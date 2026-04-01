from flask import Blueprint, render_template, session, redirect, url_for
from utils import login_required
from services.calculation_services import get_dashboard_kpis
from models import employee_model

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    company_id  = session['company_id']
    role        = session.get('role', 'Employee')

    if role == 'Admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'HR':
        return redirect(url_for('dashboard.hr_dashboard'))
    elif role == 'CHRO':
        return redirect(url_for('dashboard.chro_dashboard'))
    elif role == 'Manager':
        return redirect(url_for('dashboard.manager_dashboard'))

    kpis        = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)
    return render_template('dashboard.html', kpis=kpis, departments=departments)


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
    kpis        = get_dashboard_kpis(company_id)
    return render_template('dashboard.html', kpis=kpis, role='CHRO')