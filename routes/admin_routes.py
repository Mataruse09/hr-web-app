from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import bcrypt
import logging
from datetime import datetime

from utils import login_required, roles_required
from models import user_model, employee_model
from services.activity_service import get_activity_logs, log_activity
from services.settings_service import get_all_settings, set_setting, update_theme, initialize_default_settings
from services.rbac_service import require_admin
from services.delete_service import delete_user_permanently

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
            # ────────────────
            # 1️⃣ CREATE USER
            # ────────────────
            pass_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            created_id = user_model.create_user(
                company_id,
                username,
                email,
                full_name,
                pass_hash,
                role=role
            )

            # ⚠️ OPTIONAL: skip if you didn’t create user_roles table
            try:
                user_model.assign_role_to_user(created_id, company_id, role)
                logger.info(f"✅ User {username} (ID: {created_id}) assigned role: {role}")
            except Exception as e:
                logger.error(f"⚠️ Failed to assign role to user_roles table: {e}")

            # ────────────────
            # 2️⃣ CREATE EMPLOYEE
            # ────────────────
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
                'job_title': role,
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

            # ────────────────
            # 3️⃣ LINK USER ↔ EMPLOYEE
            # ────────────────
            employee_model.link_user(emp_id, created_id, company_id)

            flash(f'User {username} created successfully.', 'success')
            return redirect(url_for('admin.users'))

        except Exception as e:
            logger.exception(e)

            if 'emp_id' in locals():
                employee_model.delete(emp_id, company_id)

            flash('Error creating user.', 'danger')

    return render_template(
        'admin/add_user.html',
        role_options=['Admin','HR','Manager','CHRO','Employee']
    )


# ═══════════════════════════════════════════════════════════════════════════
# ✨ NEW ADMIN FEATURES - Activity Logs, Settings, Analytics
# ═══════════════════════════════════════════════════════════════════════════

@admin_bp.route('/activity-logs')
@login_required
@roles_required('Admin')
def activity_logs():
    """View activity logs for compliance and audit trail."""
    company_id = session['company_id']
    page = request.args.get('page', 1, type=int)
    limit = 50
    offset = (page - 1) * limit
    
    logs = get_activity_logs(company_id, limit=limit, offset=offset)
    return render_template('admin/activity_logs.html', logs=logs, page=page)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def system_settings():
    """Manage company system settings like theme, notifications, etc."""
    company_id = session['company_id']
    
    if request.method == 'POST':
        try:
            # Theme settings
            theme_primary = request.form.get('theme_primary_color', '#2c3e50')
            theme_secondary = request.form.get('theme_secondary_color', '#3498db')
            theme_background = request.form.get('theme_background_color', '#ecf0f1')
            
            set_setting(company_id, 'theme_primary_color', theme_primary, 'string')
            set_setting(company_id, 'theme_secondary_color', theme_secondary, 'string')
            set_setting(company_id, 'theme_background_color', theme_background, 'string')
            
            # Notification settings
            email_enabled = request.form.get('notification_email_enabled') == 'on'
            set_setting(company_id, 'notification_email_enabled', email_enabled, 'boolean')
            
            # Payroll settings
            currency = request.form.get('payroll_currency', 'USD')
            work_hours = request.form.get('work_hours_per_day', '8')
            set_setting(company_id, 'payroll_currency', currency, 'string')
            set_setting(company_id, 'work_hours_per_day', work_hours, 'string')
            
            # Log the change
            log_activity(company_id, session['user_id'], 'System settings updated')
            
            flash('System settings updated successfully!', 'success')
            return redirect(url_for('admin.system_settings'))
        
        except Exception as e:
            logger.error(f"Settings update failed: {e}")
            flash('Error updating settings.', 'danger')
    
    settings = get_all_settings(company_id)
    return render_template('admin/settings.html', settings=settings)


@admin_bp.route('/api/system-status')
@login_required
@roles_required('Admin')
def system_status():
    """API endpoint for system health and analytics."""
    company_id = session['company_id']
    
    try:
        # Get employee count
        from models.db import query
        employees = query(
            "SELECT COUNT(*) as count FROM employees_core WHERE company_id = %s",
            (company_id,), one=True
        )
        
        # Get active users
        users = query(
            "SELECT COUNT(*) as count FROM users WHERE company_id = %s AND is_active = TRUE",
            (company_id,), one=True
        )
        
        return jsonify({
            'status': 'healthy',
            'employees_count': employees['count'] if employees else 0,
            'active_users': users['count'] if users else 0,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_user(user_id):
    """Permanently delete a user (admin only). Cascades to all related tables."""
    company_id = session['company_id']
    admin_user_id = session['user_id']
    
    # Prevent admin from deleting themselves
    if user_id == admin_user_id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        result = delete_user_permanently(company_id, user_id, admin_user_id)
        
        if result['success']:
            flash(
                f"✓ {result['message']} ({result['deleted_records']} records removed)",
                'success'
            )
        else:
            flash(f"✗ {result['message']}", 'danger')
        
        return redirect(url_for('admin.users'))
    
    except Exception as e:
        logger.exception(e)
        flash('Error deleting user.', 'danger')
        return redirect(url_for('admin.users'))
