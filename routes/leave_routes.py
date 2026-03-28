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
def manage():
    company_id     = session['company_id']
    status_filter  = request.args.get('status', 'All')
    requests       = leave_model.get_requests(company_id, status_filter)
    return render_template('leave/manage.html',
                           requests=requests,
                           status_filter=status_filter)


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    company_id = session['company_id']
    employees  = employee_model.get_all(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()
        try:
            sd   = date.fromisoformat(data['start_date'])
            ed   = date.fromisoformat(data['end_date'])
            days = (ed - sd).days + 1
            if days <= 0:
                raise ValueError("End date must be after start date.")
            data['days_requested'] = days
            leave_model.create(company_id, data)
            flash('Leave request submitted successfully.', 'success')
            return redirect(url_for('leave.manage'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('leave/apply.html', employees=employees)


@leave_bp.route('/<int:req_id>/approve', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def approve(req_id):
    company_id = session['company_id']
    notes      = request.form.get('notes', '')
    leave_model.update_status(req_id, company_id, 'Approved',
                              session['user_id'], notes)
    flash('Leave request approved.', 'success')
    return redirect(url_for('leave.manage'))


@leave_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def reject(req_id):
    company_id = session['company_id']
    notes      = request.form.get('notes', 'Rejected.')
    leave_model.update_status(req_id, company_id, 'Rejected',
                              session['user_id'], notes)
    flash('Leave request rejected.', 'info')
    return redirect(url_for('leave.manage'))