from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
import bcrypt
import logging
from utils import login_required, roles_required, send_email
from models import employee_model, user_model

logger = logging.getLogger(__name__)

employee_bp = Blueprint('employees', __name__)


@employee_bp.route('/')
@login_required
def list_employees():
    company_id = session['company_id']
    search     = request.args.get('q', '').strip()
    employees  = (
        employee_model.search(company_id, search)
        if search else
        employee_model.get_all(company_id)
    )
    return render_template('employees/list.html',
                           employees=employees, search=search)


@employee_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def add_employee():
    company_id  = session['company_id']
    departments = employee_model.get_departments(company_id)
    next_code   = employee_model.get_next_employee_code(company_id)

    if request.method == 'POST':
        data = request.form.to_dict()

        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        if not email or not first_name or not last_name:
            flash('First name, last name and email are required.', 'danger')
            return render_template('employees/form.html', action='add', departments=departments, next_code=next_code, employee=None)

        employee_code = data.get('employee_code', '').strip()
        if not employee_code:
            employee_code = next_code
            data['employee_code'] = employee_code

        try:
            emp_id = employee_model.create(company_id, data)

            username = employee_code.strip().lower() if employee_code else f'emp{emp_id:04d}'
            if not username:
                username = f'emp{emp_id:04d}'

            import secrets
            from datetime import datetime, timedelta

            default_password = secrets.token_urlsafe(10)
            password_hash = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()

            # Create user account for employee
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
                raise RuntimeError('Failed to create the user account for employee.')

            user_model.assign_role_to_user(new_user_id, company_id, 'Employee')

            # =========================
            # ✅ NEW: SECURE RESET TOKEN
            # =========================
            reset_token = secrets.token_urlsafe(32)
            expiry = datetime.utcnow() + timedelta(minutes=30)

            user_model.save_reset_token(new_user_id, reset_token, expiry)

            # Send onboarding email (non-blocking)
            try:
                # ✅ FIX: use company_id instead of company_name
                reset_link = f"{request.url_root.rstrip('/')}/auth/reset-password?token={reset_token}&company_id={company_id}"

                email_body = (
                    f"Hello {first_name},\n\n"
                    f"Your employee account has been created.\n"
                    f"Username: {username}\n"
                    f"Temporary password: {default_password}\n\n"
                    f"Please set your password using this secure link (valid for 30 minutes):\n"
                    f"{reset_link}\n\n"
                    f"Thank you."
                )

                send_email(email, 'Your new HRCore employee account', email_body)

            except Exception as email_error:
                logger.warning('SMTP onboarding email failed for %s: %s', email, email_error)
                flash('Employee created; email delivery failed. Verify SMTP settings.', 'warning')

            flash('Employee added successfully and login created.', 'success')
            return redirect(url_for('employees.profile', emp_id=emp_id))

        except Exception as e:
            if 'emp_id' in locals() and emp_id:
                employee_model.delete(emp_id, company_id)
            logger.exception('Failed to add employee and user: %s', e)
            flash('Error adding employee. Please check input and ensure unique email/username.', 'danger')

    return render_template('employees/form.html',
                           action='add', departments=departments,
                           next_code=next_code, employee=None)


@employee_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR')
def edit_employee(emp_id):
    company_id  = session['company_id']
    employee    = employee_model.get_by_id(emp_id, company_id)
    departments = employee_model.get_departments(company_id)

    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    if request.method == 'POST':
            data = request.form.to_dict()
            try:
                employee_model.update(emp_id, company_id, data)

                username = data.get('employee_code', employee['employee_code']).strip().lower()
                user = user_model.get_by_username(username, company_id)
                if user:
                    try:
                        user_model.update_user_info(user['id'], company_id, data.get('email', user['email']), f"{data.get('first_name','').strip()} {data.get('last_name','').strip()}")
                    except Exception as user_err:
                        logger.warning('Failed to sync user profile for employee %s: %s', username, user_err)
                        flash('Employee saved; but user profile update failed (email may be duplicate).', 'warning')

                flash('Employee updated successfully.', 'success')
                return redirect(url_for('employees.profile', emp_id=emp_id))
            except Exception as e:
                logger.exception('Failed to update employee %s', emp_id)
                flash('Error updating employee. Please make sure the fields are correct.', 'danger')
    return render_template('employees/form.html',
                           action='edit', departments=departments,
                           employee=employee, next_code=None)


@employee_bp.route('/<int:emp_id>')
@login_required
def profile(emp_id):
    company_id = session['company_id']
    employee   = employee_model.get_by_id(emp_id, company_id)
    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))
    from models import payroll_model, leave_model, attendance_model
    from datetime import date
    comp    = payroll_model.get_compensation(emp_id, company_id)
    balance = leave_model.get_balance(emp_id, company_id, date.today().year)
    rating  = employee_model.get_average_rating(company_id, emp_id)
    return render_template('employees/profile.html',
                           employee=employee, comp=comp, balance=balance, rating=rating)


@employee_bp.route('/<int:emp_id>/rate', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'Manager', 'CHRO')
def rate_employee(emp_id):
    company_id = session['company_id']
    employee = employee_model.get_by_id(emp_id, company_id)
    if not employee:
        flash('Employee not found.', 'warning')
        return redirect(url_for('employees.list_employees'))

    score = float(request.form.get('rating', 0))
    comments = request.form.get('comments', '').strip()

    if score <= 0 or score > 5:
        flash('Rating must be between 1 and 5 stars.', 'danger')
        return redirect(url_for('employees.profile', emp_id=emp_id))

    employee_model.add_performance_review(company_id, emp_id, session['user_id'], score, comments)
    flash('Performance rating saved.', 'success')
    return redirect(url_for('employees.profile', emp_id=emp_id))


@employee_bp.route('/<int:emp_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_employee(emp_id):
    company_id = session['company_id']
    employee_model.delete(emp_id, company_id)
    flash('Employee deleted.', 'info')
    return redirect(url_for('employees.list_employees'))