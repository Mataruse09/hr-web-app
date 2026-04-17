from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
import bcrypt
from datetime import date

from models import user_model, company_model, employee_model
from services.email_service import send_admin_registration_email
from services.activity_service import log_activity
from services.settings_service import initialize_default_settings

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        company_name = (request.form.get('company') or '').strip()
        username = (request.form.get('username') or '').strip().lower()
        password = (request.form.get('password') or '').strip()

        if not company_name or not username or not password:
            flash('Company, username, and password are required.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        company = company_model.get_by_name(company_name)
        if not company:
            flash('Company not found or inactive.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        user = user_model.get_by_username(username, company['id'])

        # ✅ safer password check (PostgreSQL-safe)
        if (
            not user
            or not user.get('password_hash')
            or not bcrypt.checkpw(
                password.encode(),
                user['password_hash'].encode()
            )
        ):
            flash('Invalid credentials. Please try again.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        # ✅ clean session
        session.clear()
        session.permanent = True

        session['user_id'] = user['id']
        session['company_id'] = user['company_id']
        session['company_name'] = company['name']
        session['username'] = user['username']
        session['full_name'] = user['full_name']

        # ✅ normalize role
        role = (user.get('role') or '').strip().lower()

        role_map = {
            'admin': 'Admin',
            'hr': 'HR',
            'manager': 'Manager',
            'chro': 'CHRO',
            'company_admin': 'company_admin',
            'employee': 'Employee'
        }

        session['role'] = role_map.get(
            role,
            role.title() if role else 'Employee'
        )

        user_model.update_last_login(user['id'])
        
        # ✅ LOG LOGIN ACTIVITY
        log_activity(
            user['company_id'],
            user['id'],
            'User logged in',
            'User',
            user['id']
        )

        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('dashboard.index'))

    companies = company_model.all_active_companies()
    return render_template('login.html', companies=companies)


@auth_bp.route('/register-company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        company_name = (request.form.get('company_name') or '').strip()
        industry = (request.form.get('industry') or '').strip()
        email = (request.form.get('company_email') or '').strip().lower()
        phone = (request.form.get('company_phone') or '').strip()
        website = (request.form.get('company_website') or '').strip()
        address = (request.form.get('company_address') or '').strip()

        admin_username = (request.form.get('admin_username') or '').strip().lower()
        admin_password = (request.form.get('admin_password') or '').strip()
        admin_email = (request.form.get('admin_email') or '').strip().lower()
        admin_full_name = (request.form.get('admin_full_name') or '').strip()

        if not (company_name and admin_username and admin_password and admin_email and admin_full_name):
            flash('Company details and admin account fields are required.', 'danger')
            return render_template('register_company.html')

        existing_company = company_model.get_by_name(company_name)
        if existing_company:
            flash('Company already exists.', 'warning')
            return render_template('register_company.html')

        # ✅ CREATE COMPANY
        new_company_id = company_model.create_company(
            company_name, industry, address, phone, email, website
        )

        # ✅ CREATE ADMIN USER
        password_hash = bcrypt.hashpw(
            admin_password.encode(),
            bcrypt.gensalt()
        ).decode()

        new_user_id = user_model.create_user(
            new_company_id,
            admin_username,
            admin_email,
            admin_full_name,
            password_hash,
            role='Admin'
        )

        user_model.assign_role_to_user(new_user_id, new_company_id, 'Admin')

        # ✅ CREATE EMPLOYEE FOR ADMIN
        employee_code = employee_model.get_next_employee_code(new_company_id)

        name_parts = admin_full_name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        emp_id = employee_model.create(new_company_id, {
            'employee_code': employee_code,
            'first_name': first_name,
            'last_name': last_name,
            'email': admin_email,
            'phone': '',
            'department_id': None,
            'job_title': 'Administrator',
            'employment_type': 'Full-Time',
            'status': 'Active',
            'hire_date': date.today(),
        })

        # ✅ LINK USER ↔ EMPLOYEE
        employee_model.link_user(emp_id, new_user_id, new_company_id)

        # ✅ INITIALIZE DEFAULT SETTINGS FOR COMPANY
        initialize_default_settings(new_company_id)

        # ✅ LOG ACTIVITY
        log_activity(
            new_company_id,
            new_user_id,
            'Company registered',
            'Company',
            new_company_id,
            None,
            f"Company '{company_name}' created by {admin_full_name}"
        )

        # ✅ SEND WELCOME EMAIL TO ADMIN
        send_admin_registration_email(admin_full_name, admin_email, company_name)

        flash('Company registered successfully! Check your email for welcome message. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_company.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = (request.args.get('token') or '').strip()
    company_id = request.args.get('company_id', type=int)
    company_name = (request.args.get('company') or '').strip()

    if not token or (not company_id and not company_name):
        session.clear()
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))

    company = (
        company_model.get_by_id(company_id)
        if company_id
        else company_model.get_by_name(company_name)
    )

    if not company:
        session.clear()
        flash('Invalid company.', 'danger')
        return redirect(url_for('auth.login'))

    user = user_model.get_by_reset_token(token, company['id'])

    if not user:
        session.clear()
        flash('Reset link expired or invalid.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = (request.form.get('new_password') or '').strip()
        confirm_password = (request.form.get('confirm_password') or '').strip()

        if not new_password:
            flash('New password is required.', 'danger')
            return render_template('reset_password.html', username=user['username'])

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', username=user['username'])

        hash_pw = bcrypt.hashpw(
            new_password.encode(),
            bcrypt.gensalt()
        ).decode()

        user_model.update_password(user['id'], hash_pw)
        user_model.clear_reset_token(user['id'])

        session.clear()
        flash('Password has been updated. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', username=user['username'])


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))