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
def list_employees():
    company_id = session['company_id']
    search = request.args.get('q', '').strip()

    employees = (
        employee_model.search(company_id, search)
        if search else
        employee_model.get_all(company_id)
    )

    return render_template('employees/list.html',
                           employees=employees, search=search)


# ─────────────────────────────────────────────────────────────
# ADD EMPLOYEE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def add_employee():
    company_id = session['company_id']
    departments = employee_model.get_departments(company_id)
    next_code = employee_model.get_next_employee_code(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()

        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        if not email or not first_name or not last_name:
            flash('First name, last name and email are required.', 'danger')
            return render_template('employees/form.html',
                                   action='add', departments=departments,
                                   next_code=next_code, employee=None)

        employee_code = data.get('employee_code', '').strip()
        if not employee_code:
            employee_code = next_code
            data['employee_code'] = employee_code

        try:
            # 1️⃣ Create employee
            emp_id = employee_model.create(company_id, data)

            # safer username (avoid duplicates)
            username = f"{employee_code.lower()}_{company_id}"

            default_password = secrets.token_urlsafe(10)
            password_hash = bcrypt.hashpw(
                default_password.encode(), bcrypt.gensalt()
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

            # ✅ 3️⃣ LINK (FIXED: only once)
            employee_model.link_user(emp_id, new_user_id, company_id)

            # 4️⃣ Reset token
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(minutes=30)

            user_model.save_reset_token(new_user_id, reset_token, expiry)

            # Email
            try:
                reset_link = f"{request.url_root.rstrip('/')}/auth/reset-password?token={reset_token}&company_id={company_id}"

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

    return render_template('employees/form.html',
                           action='add', departments=departments,
                           next_code=next_code, employee=None)


# ─────────────────────────────────────────────────────────────
# MY PROFILE
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/my-profile')
@login_required
def my_profile():
    company_id = session['company_id']
    user_id = session['user_id']

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
def profile(emp_id):
    company_id = session['company_id']
    employee = employee_model.get_by_id(emp_id, company_id)

    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    from models import payroll_model, leave_model

    comp = payroll_model.get_compensation(emp_id, company_id)
    balance = leave_model.get_balance(emp_id, company_id, date.today().year)
    rating = employee_model.get_average_rating(company_id, emp_id)

    return render_template('employees/profile.html',
                           employee=employee,
                           comp=comp,
                           balance=balance,
                           rating=rating)


# ─────────────────────────────────────────────────────────────
# ✅ EDIT EMPLOYEE (NEW)
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def edit_employee(emp_id):
    company_id = session['company_id']
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

    return render_template('employees/form.html',
                           action='edit',
                           employee=employee,
                           departments=departments)


# ─────────────────────────────────────────────────────────────
# ✅ RATE EMPLOYEE (NEW)
# ─────────────────────────────────────────────────────────────
@employee_bp.route('/<int:emp_id>/rate', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'Manager', 'CHRO')
def rate_employee(emp_id):
    company_id = session['company_id']
    reviewer_id = session['user_id']

    try:
        rating = float(request.form.get('rating', 0))
        comments = request.form.get('comments', '')

        employee_model.add_performance_review(
            company_id, emp_id, reviewer_id, rating, comments
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
    company_id = session['company_id']
    employee_model.delete(emp_id, company_id)

    flash('Employee deleted.', 'info')
    return redirect(url_for('employees.list_employees'))