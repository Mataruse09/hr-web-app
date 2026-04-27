from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
from utils import login_required, roles_required
from models import attendance_model, employee_model
from datetime import date
import logging

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager', 'Employee')
def logs():
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    user_role = session.get('role', 'Employee')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    # Safer defaults (PostgreSQL friendly)
    today = date.today()
    from_date = request.args.get(
        'from',
        today.replace(day=1).isoformat()
    )
    to_date = request.args.get(
        'to',
        today.isoformat()
    )

    emp_id = request.args.get('emp_id', default=None, type=int)

    # Data access control: Employee can only view their own attendance
    if user_role == 'Employee':
        from models import employee_model as em
        employee = em.get_by_user_id(user_id, company_id)
        if not employee:
            flash('Employee record not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        emp_id = employee['id']  # Override with own ID

    # Manager can only see their department's attendance
    if user_role == 'Manager':
        from services.rbac_service import get_accessible_employees
        accessible = get_accessible_employees(user_id, user_role, company_id)
        accessible_ids = [e['id'] for e in accessible] if accessible else []
        if emp_id and emp_id not in accessible_ids:
            flash('Access denied — you can only view your team\'s attendance.', 'danger')
            return redirect(url_for('attendance.logs'))

    employees = employee_model.get_all(company_id)
    records = attendance_model.get_logs(
        company_id,
        from_date,
        to_date,
        emp_id
    )

    return render_template(
        'attendance/logs.html',
        records=records,
        employees=employees,
        from_date=from_date,
        to_date=to_date,
        selected_emp=emp_id,
        is_readonly=(user_role == 'Employee')
    )


@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'company_admin')
def mark():
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    today = date.today().isoformat()

    # Only get active employees for attendance marking
    employees = employee_model.get_all(company_id, status='Active')
    existing = attendance_model.get_by_date(company_id, today)

    # Faster lookup
    existing_map = {r['employee_id']: r for r in existing}

    if request.method == 'POST':
        work_date = request.form.get('work_date') or today
        saved = 0

        for emp in employees:
            eid = emp['id']

            status = request.form.get(f'status_{eid}')
            if not status:
                continue

            check_in = request.form.get(f'check_in_{eid}') or None
            check_out = request.form.get(f'check_out_{eid}') or None
            notes = request.form.get(f'notes_{eid}') or None

            attendance_model.upsert(
                company_id,
                eid,
                work_date,
                check_in,
                check_out,
                status,
                notes,
                user_id,
            )

            saved += 1

        # Invalidate KPI cache for this company after attendance update
        from services.calculation_services import invalidate_company_cache
        invalidate_company_cache(company_id)
        logger.info(f"Invalidated KPI cache for company {company_id} after attendance update")
        
        flash(f'Attendance saved for {saved} employee(s).', 'success')
        return redirect(url_for('attendance.mark'))

    return render_template(
        'attendance/mark.html',
        employees=employees,
        existing_map=existing_map,
        today=today
    )