from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import attendance_model, employee_model
from datetime import date

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
@login_required
def logs():
    company_id = session['company_id']
    from_date  = request.args.get('from', date.today().replace(day=1).isoformat())
    to_date    = request.args.get('to',   date.today().isoformat())
    emp_id     = request.args.get('emp_id', type=int)
    employees  = employee_model.get_all(company_id)
    records    = attendance_model.get_logs(company_id, from_date, to_date, emp_id)
    return render_template('attendance/logs.html',
                           records=records, employees=employees,
                           from_date=from_date, to_date=to_date,
                           selected_emp=emp_id)


@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'company_admin')
def mark():
    company_id  = session['company_id']
    user_id     = session['user_id']
    today       = date.today().isoformat()
    employees   = employee_model.get_all(company_id)
    existing    = attendance_model.get_by_date(company_id, today)
    existing_map = {r['employee_id']: r for r in existing}

    if request.method == 'POST':
        work_date = request.form.get('work_date', today)
        saved = 0
        for emp in employees:
            eid     = emp['id']
            status  = request.form.get(f'status_{eid}')
            if not status:
                continue
            check_in  = request.form.get(f'check_in_{eid}', '')
            check_out = request.form.get(f'check_out_{eid}', '')
            notes     = request.form.get(f'notes_{eid}', '')
            attendance_model.upsert(
                company_id, eid, work_date,
                check_in or None, check_out or None,
                status, notes, user_id,
            )
            saved += 1
        flash(f'Attendance saved for {saved} employee(s).', 'success')
        return redirect(url_for('attendance.mark'))

    return render_template('attendance/mark.html',
                           employees=employees,
                           existing_map=existing_map,
                           today=today)