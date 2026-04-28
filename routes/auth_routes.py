from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
    current_app
)
import bcrypt
import logging
from datetime import date, datetime, timedelta
from functools import wraps

from models import user_model, company_model, employee_model
from models.db import query, mutate
from services.email_service import send_admin_registration_email, send_password_reset_email
from services.activity_service import log_activity
from services.settings_service import initialize_default_settings

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Security: Track failed login attempts per IP
failed_login_attempts = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 15  # minutes


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        company_name = (request.form.get('company') or '').strip()
        username = (request.form.get('username') or '').strip().lower()
        password = (request.form.get('password') or '').strip()
        
        # Get client IP for security tracking
        client_ip = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()

        # Check if IP is temporarily locked out due to too many failed attempts
        if client_ip in failed_login_attempts:
            attempts_data = failed_login_attempts[client_ip]
            if attempts_data['count'] >= MAX_FAILED_ATTEMPTS:
                # Check if lockout has expired
                lockout_end = attempts_data.get('lockout_until')
                if lockout_end and datetime.utcnow() < lockout_end:
                    remaining = (lockout_end - datetime.utcnow()).seconds // 60
                    flash(f'Too many failed login attempts. Please try again in {remaining} minutes.', 'danger')
                    companies = company_model.all_active_companies()
                    return render_template('login.html', companies=companies)
                else:
                    # Lockout expired, reset attempts
                    del failed_login_attempts[client_ip]

        if not company_name or not username or not password:
            flash('Company, username, and password are required.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        company = company_model.get_by_name(company_name)
        if not company:
            flash('Company not found or inactive.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        # Check if company is blocked/inactive
        if not company.get('is_active', True):
            flash('Your company account has been suspended. Please contact support.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)
        
        # Check for ban reason if exists
        if company.get('ban_reason'):
            flash(f'Access denied: {company.get("ban_reason")}. Please contact support.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

        user = user_model.get_by_username(username, company['id'])

        if user:
            # ✅ safer password check (PostgreSQL-safe)
            if not user or not user.get('password_hash'):
                flash('Invalid credentials. Please try again.', 'danger')
                companies = company_model.all_active_companies()
                return render_template('login.html', companies=companies)
            
            # Handle password hash that may already be bytes or string
            password_hash = user['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            try:
                password_matches = bcrypt.checkpw(password.encode('utf-8'), password_hash)
            except Exception as e:
                flash('Invalid credentials. Please try again.', 'danger')
                companies = company_model.all_active_companies()
                return render_template('login.html', companies=companies)
            
            if not password_matches:
                # Track failed login attempt for security
                if client_ip not in failed_login_attempts:
                    failed_login_attempts[client_ip] = {'count': 0, 'lockout_until': None}
                
                failed_login_attempts[client_ip]['count'] += 1
                
                # If too many failed attempts, lock out the IP
                if failed_login_attempts[client_ip]['count'] >= MAX_FAILED_ATTEMPTS:
                    failed_login_attempts[client_ip]['lockout_until'] = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION)
                
                # Log the failed login attempt
                if company:
                    log_activity(
                        company['id'],
                        user['id'] if user else None,
                        f'Failed login attempt from IP {client_ip}',
                        'Security',
                        user['id'] if user else None
                    )
                
                flash('Invalid credentials. Please try again.', 'danger')
                companies = company_model.all_active_companies()
                return render_template('login.html', companies=companies)

            # Check if user has a linked employee and if they are active
            from models import employee_model as em
            employee = em.get_by_user_id(user['id'], company['id'])
            if employee and employee.get('status') != 'Active':
                flash('Your account has been deactivated. Please contact your administrator.', 'warning')
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

            # If role is empty or None, check user_roles table
            if not role:
                from models import user_model as um
                user_roles = um.get_user_roles(user['id'], company['id'])
                if user_roles and len(user_roles) > 0:
                    role = user_roles[0]['role'].strip().lower()

            role_map = {
                'admin': 'Admin',
                'hr': 'HR',
                'manager': 'Manager',
                'chro': 'CHRO',
                'company_admin': 'company_admin',
                'employee': 'Employee',
                'emp': 'Employee',
                'staff': 'Employee',
                'user': 'Employee'
            }

            session['role'] = role_map.get(role, 'Employee')

            # Reset failed login attempts on successful login
            if client_ip in failed_login_attempts:
                del failed_login_attempts[client_ip]

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
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies)

    companies = company_model.all_active_companies()
    return render_template('login.html', companies=companies)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request."""
    if request.method == 'POST':
        company_name = (request.form.get('company') or '').strip()
        username = (request.form.get('username') or '').strip().lower()
        email = (request.form.get('email') or '').strip().lower()
        
        if not company_name or not username:
            flash('Company and username are required.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies, show_forgot=True)
        
        company = company_model.get_by_name(company_name)
        if not company:
            flash('Company not found.', 'danger')
            companies = company_model.all_active_companies()
            return render_template('login.html', companies=companies, show_forgot=True)
        
        user = user_model.get_by_username(username, company['id'])
        if not user:
            flash('If an account exists with that username, a reset link will be sent.', 'info')
            return redirect(url_for('auth.login'))
        
        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        from datetime import datetime, timedelta
        expiry = datetime.utcnow() + timedelta(minutes=30)
        
        user_model.save_reset_token(user['id'], reset_token, expiry)
        
        # Build reset link
        reset_link = f"{request.url_root.rstrip('/')}/auth/reset-password?token={reset_token}&company_id={company['id']}"
        
        # Send password reset email
        try:
            send_password_reset_email(
                user['full_name'],
                user['email'],
                company['name'],
                reset_link
            )
            flash('If an account exists, a password reset link has been sent to your email.', 'info')
        except Exception as e:
            logger.warning(f"Failed to send password reset email: {e}")
            flash('If an account exists, a password reset link has been sent to your email.', 'info')
        
        return redirect(url_for('auth.login'))
    
    companies = company_model.all_active_companies()
    return render_template('login.html', companies=companies, show_forgot=True)


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
        terms_accepted = request.form.get('terms_accepted') == 'on'

        if not (company_name and admin_username and admin_password and admin_email and admin_full_name):
            flash('Company details and admin account fields are required.', 'danger')
            return render_template('register_company.html')

        # Check if terms are accepted
        if not terms_accepted:
            flash('You must agree to the Terms and Conditions, Privacy Policy, and Acceptable Use Policy to register.', 'warning')
            return render_template('register_company.html')

        existing_company = company_model.get_by_name(company_name)
        if existing_company:
            flash('Company already exists.', 'warning')
            return render_template('register_company.html')

        # ✅ CREATE COMPANY
        new_company_id = company_model.create_company(
            company_name, industry, address, phone, email, website, terms_accepted
        )

        # ✅ CREATE ADMIN USER
        password_hash = bcrypt.hashpw(
            admin_password.encode(),
            bcrypt.gensalt()
        ).decode()

        try:
            new_user_id = user_model.create_user(
                new_company_id,
                admin_username,
                admin_email,
                admin_full_name,
                password_hash,
                role='Admin'
            )
        except ValueError as e:
            # Username collision - try auto-generating one
            logger.warning(f"Username collision during registration: {e}. Attempting auto-generate.")
            try:
                # Generate unique username: username_companyid or username1, username2, etc
                base_username = admin_username
                counter = 1
                while counter < 100:
                    test_username = f"{base_username}{counter}"
                    test_user = user_model.get_by_username(test_username, new_company_id)
                    if not test_user:
                        new_user_id = user_model.create_user(
                            new_company_id,
                            test_username,
                            admin_email,
                            admin_full_name,
                            password_hash,
                            role='Admin'
                        )
                        flash(f'Username "{admin_username}" was taken. Using "{test_username}" instead.', 'info')
                        break
                    counter += 1
                else:
                    flash('Could not generate a unique username. Please try again with a different username.', 'danger')
                    return render_template('register_company.html')
            except Exception as e2:
                logger.error(f"Failed to create admin user: {e2}")
                flash('Failed to create admin account. Please try again.', 'danger')
                return render_template('register_company.html')
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            flash(f'Failed to create admin account: {str(e)}', 'danger')
            return render_template('register_company.html')

        # ✅ ASSIGN ROLE TO USER_ROLES TABLE
        try:
            user_model.assign_role_to_user(new_user_id, new_company_id, 'Admin')
        except Exception as e:
            logger.error(f"⚠️ Failed to assign role to user_roles table: {e}")

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
        try:
            initialize_default_settings(new_company_id)
        except Exception as e:
            logger.warning(f"Failed to initialize settings for company {new_company_id}: {e}")

        # ✅ LOG ACTIVITY
        try:
            log_activity(
                new_company_id,
                new_user_id,
                'Company registered',
                'Company',
                new_company_id,
                None,
                f"Company '{company_name}' created by {admin_full_name}"
            )
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")

        # ✅ SEND WELCOME EMAIL TO ADMIN
        try:
            send_admin_registration_email(admin_full_name, admin_email, company_name)
        except Exception as e:
            logger.warning(f"Failed to send registration email: {e}")

        # ✅ SEND NOTIFICATION TO SUPPORT EMAIL
        try:
            from services.email_service import send_email
            support_subject = f"New Company Registration - {company_name}"
            support_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1a2b4a;">New Company Registered!</h2>
                    
                    <p>A new company has registered on <strong>MatinexHR</strong>.</p>
                    
                    <h3>Company Details:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Company Name:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{company_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Industry:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{industry}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Admin Name:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{admin_full_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Admin Email:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{admin_email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Phone:</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{phone}</td>
                        </tr>
                    </table>
                    
                    <p style="margin-top: 20px;">This is an automated notification from the MatinexHR system.</p>
                </div>
            </body>
            </html>
            """
            send_email('tinashemataruse226@gmail.com', support_subject, support_body, is_html=True)
        except Exception as e:
            logger.warning(f"Failed to send support notification email: {e}")

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