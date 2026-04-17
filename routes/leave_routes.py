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
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def manage():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    status_filter = (request.args.get('status') or 'All').strip()

    requests = leave_model.get_requests(company_id, status_filter)

    return render_template(
        'leave/manage.html',
        requests=requests,
        status_filter=status_filter
    )


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employees = employee_model.get_all(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()

        try:
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
        employees=employees
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