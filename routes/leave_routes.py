from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import leave_model, employee_model
from datetime import date

leave_bp = Blueprint('leave', __name__)


@leave_bp.route('/')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager', 'Employee')
def manage():
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    user_role = session.get('role', 'Employee')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    status_filter = (request.args.get('status') or 'All').strip()

    # Data access control: Employee can only see their own leave requests
    if user_role == 'Employee':
        from models import employee_model as em
        employee = em.get_by_user_id(user_id, company_id)
        if not employee:
            flash('Employee record not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        # Filter to only this employee's requests
        all_requests = leave_model.get_requests(company_id, status_filter)
        requests = [r for r in (all_requests or []) if r.get('employee_id') == employee['id']]
    elif user_role == 'Manager':
        # Manager can see their team's leave requests
        from services.rbac_service import get_accessible_employees
        accessible = get_accessible_employees(user_id, user_role, company_id)
        accessible_ids = [e['id'] for e in accessible] if accessible else []
        all_requests = leave_model.get_requests(company_id, status_filter)
        requests = [r for r in (all_requests or []) if r.get('employee_id') in accessible_ids]
    else:
        # Admin, HR, CHRO see all
        requests = leave_model.get_requests(company_id, status_filter)

    return render_template(
        'leave/manage.html',
        requests=requests,
        status_filter=status_filter,
        is_readonly=(user_role == 'Employee')
    )


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager', 'Employee')
def apply():
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    user_role = session.get('role', 'Employee')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    # Get employee record
    user_employee = employee_model.get_by_user_id(user_id, company_id)
    if not user_employee:
        flash('Employee record not found.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Employee can only apply for themselves
    if user_role == 'Employee':
        employees = [user_employee]
    else:
        employees = employee_model.get_all(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()

        try:
            # Validate data ownership: Employee can only apply for themselves
            employee_id = int(data.get('employee_id', 0))
            if user_role == 'Employee' and employee_id != user_employee['id']:
                flash('You can only apply leave for yourself.', 'danger')
                return redirect(url_for('leave.apply'))

            start_date = (data.get('start_date') or '').strip()
            end_date = (data.get('end_date') or '').strip()

            if not start_date or not end_date:
                raise ValueError("Start date and end date are required.")

            sd = date.fromisoformat(start_date)
            ed = date.fromisoformat(end_date)

            days = (ed - sd).days + 1

            if days <= 0:
                raise ValueError("End date must be after start date.")

            data['days_requested'] = days

            leave_model.create(company_id, data)

            flash('Leave request submitted successfully.', 'success')
            return redirect(url_for('leave.manage'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template(
        'leave/apply.html',
        employees=employees,
        is_employee=(user_role == 'Employee')
    )


@leave_bp.route('/<int:req_id>/approve', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def approve(req_id):
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    notes = (request.form.get('notes') or '').strip() or None

    leave_model.update_status(
        req_id,
        company_id,
        'Approved',
        user_id,
        notes
    )

    flash('Leave request approved.', 'success')
    return redirect(url_for('leave.manage'))


@leave_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def reject(req_id):
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    notes = (request.form.get('notes') or 'Rejected.').strip()

    leave_model.update_status(
        req_id,
        company_id,
        'Rejected',
        user_id,
        notes
    )

    flash('Leave request rejected.', 'info')
    return redirect(url_for('leave.manage'))