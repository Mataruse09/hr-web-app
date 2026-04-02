from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt
from utils import login_required, roles_required
from models import user_model

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
            return render_template('admin/add_user.html', role_options=['Admin','HR','Manager','CHRO','Employee'])

        if user_model.get_by_username(username, company_id):
            flash('Username already exists.', 'warning')
            return render_template('admin/add_user.html', role_options=['Admin','HR','Manager','CHRO','Employee'])

        pass_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        created_id = user_model.create_user(company_id, username, email, full_name, pass_hash, role=role)
        user_model.assign_role_to_user(created_id, company_id, role)

        flash(f'User {username} created with role {role}.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/add_user.html', role_options=['Admin','HR','Manager','CHRO','Employee'])
