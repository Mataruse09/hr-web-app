from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
import bcrypt
import logging
import secrets
from datetime import datetime, timedelta, date

from utils import login_required, roles_required, send_email
from models import employee_model, user_model

logger = logging.getLogger(__name__)

employee_bp = Blueprint('employees', __name__)


# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager', 'Employee')
def list_employees():
    company_id = session.get('company_id')
    user_role = session.get('role')
    user_id = session.get('user_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    search = (request.args.get('q') or '').strip()

    # Get all employees for company
    all_employees = (
        employee_model.search(company_id, search)
        if search else
        employee_model.get_all(company_id)
    )

    # Filter based on role
    employees = all_employees
    if user_role == 'Employee':
        # Employees only see themselves
        employees = [e for e in (all_employees or []) if e.get('user_id') == user_id]
    elif user_role == 'Manager':
        # TODO: Managers see only their department (requires department_id in session or lookup)
        # For now, showing all (should filter by manager's department)
        employees = all_employees

    return render_template(
        'employees/list.html',
        employees=employees,
        search=search
    )


# ─────────────────────────────────────────────────────────────
# ADD EMPLOYEE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def add_employee():
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    departments = employee_model.get_departments(company_id)
    next_code = employee_model.get_next_employee_code(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()

        email = (data.get('email') or '').strip().lower()
        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()

        if not email or not first_name or not last_name:
            flash('First name, last name and email are required.', 'danger')
            return render_template(
                'employees/form.html',
                action='add',
                departments=departments,
                next_code=next_code,
                employee=None
            )

        employee_code = (data.get('employee_code') or '').strip()
        if not employee_code:
            employee_code = next_code
            data['employee_code'] = employee_code

        try:
            # 1️⃣ Create employee
            emp_id = employee_model.create(company_id, data)

            username = f"{employee_code.lower()}_{company_id}"

            default_password = secrets.token_urlsafe(10)
            password_hash = bcrypt.hashpw(
                default_password.encode(),
                bcrypt.gensalt()
            ).decode()

            # 2️⃣ Create user
            new_user_id = user_model.create_user(
                company_id,
                username,
                email,
                f"{first_name} {last_name}",
                password_hash,
                role='Employee'
            )

            if not new_user_id:
                employee_model.delete(emp_id, company_id)
                raise RuntimeError('Failed to create user account.')

            user_model.assign_role_to_user(new_user_id, company_id, 'Employee')

            # 3️⃣ LINK
            employee_model.link_user(emp_id, new_user_id, company_id)

            # 4️⃣ Reset token
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(minutes=30)

            user_model.save_reset_token(new_user_id, reset_token, expiry)

            # Email
            try:
                reset_link = (
                    f"{request.url_root.rstrip('/')}"
                    f"/auth/reset-password?token={reset_token}&company_id={company_id}"
                )

                email_body = (
                    f"Hello {first_name},\n\n"
                    f"Your employee account has been created.\n"
                    f"Username: {username}\n"
                    f"Temporary password: {default_password}\n\n"
                    f"Set password (valid 30 min):\n{reset_link}\n\n"
                )

                send_email(email, 'Your new HRCore account', email_body)

            except Exception as email_error:
                logger.warning('SMTP failed: %s', email_error)

            flash('Employee added successfully.', 'success')
            return redirect(url_for('employees.profile', emp_id=emp_id))

        except Exception as e:
            if 'emp_id' in locals():
                employee_model.delete(emp_id, company_id)

            logger.exception(e)
            flash('Error adding employee.', 'danger')

    return render_template(
        'employees/form.html',
        action='add',
        departments=departments,
        next_code=next_code,
        employee=None
    )


# ─────────────────────────────────────────────────────────────
# MY PROFILE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/my-profile')
@login_required
def my_profile():
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if not company_id or not user_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employee = employee_model.get_by_user_id(user_id, company_id)

    if not employee:
        flash('Profile not linked to employee.', 'warning')
        return redirect(url_for('dashboard.index'))

    return redirect(url_for('employees.profile', emp_id=employee['id']))


# ─────────────────────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager', 'Employee')
def profile(emp_id):
    company_id = session.get('company_id')
    user_id = session.get('user_id')
    user_role = session.get('role')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employee = employee_model.get_by_id(emp_id, company_id)

    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    # Access control: Employees can only view themselves
    if user_role == 'Employee' and employee.get('user_id') != user_id:
        flash('You do not have permission to view this profile.', 'danger')
        return redirect(url_for('employees.list_employees'))

    from models import payroll_model, leave_model

    comp = payroll_model.get_compensation(emp_id, company_id)
    balance = leave_model.get_balance(emp_id, company_id, date.today().year)
    rating = employee_model.get_average_rating(company_id, emp_id)

    # Determine if sensitive data should be shown
    show_sensitive_data = (
        user_role in ['Admin', 'HR', 'CHRO'] or 
        employee.get('user_id') == user_id
    )

    return render_template(
        'employees/profile.html',
        employee=employee,
        comp=comp,
        balance=balance,
        rating=rating,
        show_sensitive_data=show_sensitive_data
    )


# ─────────────────────────────────────────────────────────────
# EDIT EMPLOYEE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def edit_employee(emp_id):
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employee = employee_model.get_by_id(emp_id, company_id)
    departments = employee_model.get_departments(company_id)

    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    if request.method == 'POST':
        data = request.form.to_dict()
        employee_model.update(emp_id, company_id, data)

        flash('Employee updated successfully.', 'success')
        return redirect(url_for('employees.profile', emp_id=emp_id))

    return render_template(
        'employees/form.html',
        action='edit',
        employee=employee,
        departments=departments
    )


# ─────────────────────────────────────────────────────────────
# RATE EMPLOYEE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>/rate', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'Manager', 'CHRO')
def rate_employee(emp_id):
    company_id = session.get('company_id')
    reviewer_id = session.get('user_id')

    if not company_id or not reviewer_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    try:
        rating = float(request.form.get('rating') or 0)
        comments = (request.form.get('comments') or '').strip()

        employee_model.add_performance_review(
            company_id,
            emp_id,
            reviewer_id,
            rating,
            comments
        )

        flash('Performance rating added.', 'success')

    except Exception as e:
        logger.exception(e)
        flash('Error saving rating.', 'danger')

    return redirect(url_for('employees.profile', emp_id=emp_id))


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_employee(emp_id):
    company_id = session.get('company_id')

    if not company_id:
        flash("Session expired. Please login again.", "danger")
        return redirect(url_for('auth.login'))

    employee_model.delete(emp_id, company_id)

    flash('Employee deleted.', 'info')
    return redirect(url_for('employees.list_employees'))