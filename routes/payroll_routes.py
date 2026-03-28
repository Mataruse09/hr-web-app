from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import payroll_model, employee_model
from services.calculation_services import build_payroll_for_employee
from datetime import date

payroll_bp = Blueprint('payroll', __name__)


@payroll_bp.route('/')
@login_required
def list_payroll():
    company_id = session['company_id']
    period     = request.args.get('period', date.today().strftime('%Y-%m'))
    runs       = payroll_model.get_runs(company_id, period)
    return render_template('payroll/list.html', runs=runs, period=period)


@payroll_bp.route('/process', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def process():
    company_id = session['company_id']
    employees  = employee_model.get_all(company_id)
    active_emps = [e for e in employees if e['status'] == 'Active']

    if request.method == 'POST':
        pay_period   = request.form.get('pay_period')
        working_days = int(request.form.get('working_days', 22))
        processed    = 0
        errors       = 0

        for emp in active_emps:
            bonus = float(request.form.get(f'bonus_{emp["id"]}', 0) or 0)
            payload = build_payroll_for_employee(
                company_id  = company_id,
                employee_id = emp['id'],
                pay_period  = pay_period,
                processed_by= session['user_id'],
                bonus       = bonus,
                working_days= working_days,
            )
            if payload:
                try:
                    payroll_model.upsert_run(
                        company_id, emp['id'], pay_period, payload
                    )
                    processed += 1
                except Exception:
                    errors += 1

        flash(
            f'Payroll processed: {processed} records saved'
            + (f', {errors} errors.' if errors else '.'),
            'success' if not errors else 'warning',
        )
        return redirect(url_for('payroll.list_payroll', period=pay_period))

    current_period = date.today().strftime('%Y-%m')
    return render_template('payroll/process.html',
                           employees=active_emps,
                           current_period=current_period)


@payroll_bp.route('/compensation/<int:emp_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def compensation(emp_id):
    company_id = session['company_id']
    emp        = employee_model.get_by_id(emp_id, company_id)
    if not emp:
        flash('Employee not found.', 'warning')
        return redirect(url_for('payroll.list_payroll'))

    comp = payroll_model.get_compensation(emp_id, company_id)

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            payroll_model.save_compensation(company_id, emp_id, data)
            flash('Compensation saved.', 'success')
            return redirect(url_for('employees.profile', emp_id=emp_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('payroll/process.html',
                           mode='compensation',
                           employee=emp, comp=comp)