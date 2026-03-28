from flask import Blueprint, render_template, session
from utils import login_required
from services.calculation_services import get_dashboard_kpis
from models import employee_model

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    company_id  = session['company_id']
    kpis        = get_dashboard_kpis(company_id)
    departments = employee_model.get_departments(company_id)
    return render_template('dashboard.html', kpis=kpis, departments=departments)