from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
import bcrypt
from models import user_model, company_model

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        company_name = request.form.get('company', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

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

        if not user or not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            flash('Invalid credentials. Please try again.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        session.permanent = True
        session['user_id'] = user['id']
        session['company_id'] = user['company_id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']

        user_model.update_last_login(user['id'])
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('dashboard.index'))

    companies = company_model.all_active_companies()
    return render_template('login.html', companies=companies)


@auth_bp.route('/register-company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()
        email = request.form.get('company_email', '').strip()
        phone = request.form.get('company_phone', '').strip()
        website = request.form.get('company_website', '').strip()
        address = request.form.get('company_address', '').strip()

        admin_username = request.form.get('admin_username', '').strip()
        admin_password = request.form.get('admin_password', '').strip()
        admin_email = request.form.get('admin_email', '').strip()
        admin_full_name = request.form.get('admin_full_name', '').strip()

        if not (company_name and admin_username and admin_password and admin_email and admin_full_name):
            flash('Company details and admin account fields are required.', 'danger')
            return render_template('register_company.html')

        existing_company = company_model.get_by_name(company_name)
        if existing_company:
            flash('Company already exists.', 'warning')
            return render_template('register_company.html')

        new_company_id = company_model.create_company(
            company_name, industry, address, phone, email, website
        )

        password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        user_model.create_user(new_company_id, admin_username, admin_email, admin_full_name, password_hash, role='Admin')

        flash('Company registered successfully. Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_company.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))