from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt
import logging
from datetime import datetime

from utils import login_required, roles_required
from models import user_model, employee_model

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users')
@login_required
@roles_required('Admin', 'company_admin')
def users():
    company_id = session['company_id']
    users = user_model.get_all_users(company_id)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'company_admin')
def add_user():
    company_id = session['company_id']

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', '').strip()

        if not (username and password and email and full_name and role):
            flash('All fields are required.', 'danger')
            return render_template(
                'admin/add_user.html',
                role_options=['Admin','HR','Manager','CHRO','Employee']
            )

        if user_model.get_by_username(username, company_id):
            flash('Username already exists.', 'warning')
            return render_template(
                'admin/add_user.html',
                role_options=['Admin','HR','Manager','CHRO','Employee']
            )

        try:
            # ─────────────────────────────────────────
            # 1️⃣ CREATE USER
            # ─────────────────────────────────────────
            pass_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            created_id = user_model.create_user(
                company_id,
                username,
                email,
                full_name,
                pass_hash,
                role=role
            )

            user_model.assign_role_to_user(created_id, company_id, role)

            # ─────────────────────────────────────────
            # 2️⃣ CREATE EMPLOYEE (FIXED SAFELY)
            # ─────────────────────────────────────────
            next_code = employee_model.get_next_employee_code(company_id)

            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            emp_id = employee_model.create(company_id, {
                'employee_code': next_code,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': '',
                'department_id': None,
                'job_title': role,  # simple + useful
                'employment_type': 'Full-Time',
                'status': 'Active',
                'hire_date': datetime.utcnow().date(),
                'date_of_birth': None,
                'gender': 'Prefer not to say',
                'nationality': '',
                'address': '',
                'emergency_contact_name': '',
                'emergency_contact_phone': '',
            })

            # ─────────────────────────────────────────
            # 3️⃣ LINK USER ↔ EMPLOYEE
            # ─────────────────────────────────────────
            employee_model.link_user(emp_id, created_id, company_id)

            flash(f'User {username} created successfully.', 'success')
            return redirect(url_for('admin.users'))

        except Exception as e:
            logger.exception(e)

            # rollback employee if created
            if 'emp_id' in locals():
                employee_model.delete(emp_id, company_id)

            flash('Error creating user.', 'danger')

    return render_template(
        'admin/add_user.html',
        role_options=['Admin','HR','Manager','CHRO','Employee']
    )