from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import payroll_model, employee_model
from models.db import begin_transaction, commit_transaction, rollback_transaction
from services.calculation_services import build_payroll_for_employee
from datetime import date
import logging

logger = logging.getLogger(__name__)

payroll_bp = Blueprint('payroll', __name__)


@payroll_bp.route('/')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def list_payroll():
    """List payroll runs. CHRO can view only, HR/Admin can view and edit."""
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    period = (request.args.get('period') or date.today().strftime('%Y-%m')).strip()
    runs = payroll_model.get_runs(company_id, period)

    # Add read-only flag for CHRO
    user_role = session.get('role', 'Employee').strip().lower()
    is_readonly = user_role == 'chro'

    return render_template(
        'payroll/list.html',
        runs=runs,
        period=period,
        is_readonly=is_readonly
    )


@payroll_bp.route('/process', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')  # CHRO cannot process/approve payroll, only view
def process():
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employees = employee_model.get_all(company_id)
    active_emps = [e for e in employees if e.get('status') == 'Active']

    if request.method == 'POST':
        pay_period = (request.form.get('pay_period') or '').strip()

        if not pay_period:
            flash('Pay period is required.', 'danger')
            return redirect(url_for('payroll.process'))

        try:
            working_days = int(request.form.get('working_days') or 22)
        except ValueError:
            working_days = 22

        # Start transaction for batch payroll processing
        conn = None
        processed = 0
        errors = 0

        try:
            conn = begin_transaction()
            
            for emp in active_emps:
                try:
                    bonus = float(request.form.get(f'bonus_{emp["id"]}') or 0)

                    payload = build_payroll_for_employee(
                        company_id=company_id,
                        employee_id=emp['id'],
                        pay_period=pay_period,
                        processed_by=user_id,
                        bonus=bonus,
                        working_days=working_days,
                    )

                    if payload:
                        payroll_model.upsert_run(
                            company_id,
                            emp['id'],
                            pay_period,
                            payload
                        )
                        processed += 1

                except Exception as e:
                    errors += 1
                    logger.error(f"Payroll error for employee {emp['id']}: {str(e)}")

            # Commit if no errors, else rollback
            if errors == 0:
                commit_transaction(conn)
                flash(f'Payroll processed: {processed} records saved.', 'success')
            else:
                rollback_transaction(conn)
                flash(
                    f'Payroll processing completed with {errors} errors. All changes rolled back for consistency.',
                    'error'
                )

        except Exception as e:
            if conn:
                rollback_transaction(conn)
            logger.error(f"Payroll batch processing error: {str(e)}")
            flash(f'Payroll batch processing error: {str(e)}', 'danger')

        return redirect(url_for('payroll.list_payroll', period=pay_period))

    current_period = date.today().strftime('%Y-%m')

    return render_template(
        'payroll/process.html',
        employees=active_emps,
        current_period=current_period
    )


@payroll_bp.route('/compensation/<int:emp_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')  # CHRO cannot edit compensation
def compensation(emp_id):
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    emp = employee_model.get_by_id(emp_id, company_id)

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

    return render_template(
        'payroll/process.html',
        mode='compensation',
        employee=emp,
        comp=comp
    )