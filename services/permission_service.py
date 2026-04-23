"""
Enhanced Permission Service - Specialized Decorators for Role-Based Access Control
Extends rbac_service.py with application-specific permission checks
"""
from functools import wraps
from flask import session, redirect, url_for, flash, jsonify
import logging
from models.db import query

logger = logging.getLogger(__name__)


# ============================================================================
# PERMISSION VALIDATION FUNCTIONS
# ============================================================================

def is_payroll_restricted(role: str) -> bool:
    """Check if role cannot access payroll. Returns True if Manager or Employee."""
    return role.lower() in ['manager', 'employee']


def is_delete_restricted(role: str) -> bool:
    """Check if role cannot permanently delete employees. Returns True if HR (not Admin)."""
    return role.lower() == 'hr'


def is_settings_restricted(role: str) -> bool:
    """Check if role cannot access system settings. Returns True if not Admin."""
    return role.lower() != 'admin'


def get_permitted_features(role: str) -> dict:
    """
    Return dict of features accessible by role.
    Helps with dynamic menu generation.
    """
    role_lower = role.lower()

    features = {
        'admin': {
            'dashboard': True,
            'employees': {'view': True, 'edit': True, 'delete': True},
            'attendance': {'view': True, 'mark': True},
            'leave': {'view': True, 'approve': True},
            'payroll': {'view': True, 'edit': True, 'approve': True},
            'appraisals': {'view': True, 'create': True, 'review': True},
            'gamification': {'view': True, 'award': True, 'manage': True},
            'compliance': {'view': True, 'assign': True, 'manage': True},
            'forecasting': {'view': True, 'create': True},
            'attrition': {'view': True, 'record': True, 'analytics': True},
            'activity_logs': True,
            'user_management': True,
            'system_settings': True,
        },
        'chro': {
            'dashboard': True,
            'employees': {'view': True, 'edit': False, 'delete': False},
            'attendance': {'view': True, 'mark': False},
            'leave': {'view': True, 'approve': False},
            'payroll': {'view': True, 'edit': False, 'approve': False},
            'appraisals': {'view': True, 'create': True, 'review': True},
            'gamification': {'view': True, 'award': True, 'manage': False},
            'compliance': {'view': True, 'assign': True, 'manage': True},
            'forecasting': {'view': True, 'create': True},
            'attrition': {'view': True, 'record': False, 'analytics': True},
            'activity_logs': True,
            'user_management': False,
            'system_settings': False,
        },
        'hr': {
            'dashboard': True,
            'employees': {'view': True, 'edit': True, 'delete': False},
            'attendance': {'view': True, 'mark': True},
            'leave': {'view': True, 'approve': True},
            'payroll': {'view': True, 'edit': True, 'approve': True},
            'appraisals': {'view': True, 'create': True, 'review': True},
            'gamification': {'view': True, 'award': True, 'manage': True},
            'compliance': {'view': True, 'assign': True, 'manage': True},
            'forecasting': {'view': True, 'create': True},
            'attrition': {'view': True, 'record': True, 'analytics': True},
            'activity_logs': True,
            'user_management': False,
            'system_settings': False,
        },
        'manager': {
            'dashboard': True,
            'employees': {'view': True, 'edit': True, 'delete': False},
            'attendance': {'view': True, 'mark': True},
            'leave': {'view': True, 'approve': True},
            'payroll': {'view': False, 'edit': False, 'approve': False},
            'appraisals': {'view': True, 'create': True, 'review': True},
            'gamification': {'view': True, 'award': True, 'manage': False},
            'compliance': {'view': True, 'assign': True, 'manage': False},
            'forecasting': {'view': False, 'create': False},
            'attrition': {'view': False, 'record': False, 'analytics': False},
            'activity_logs': False,
            'user_management': False,
            'system_settings': False,
        },
        'employee': {
            'dashboard': True,
            'employees': {'view': 'own_only', 'edit': False, 'delete': False},
            'attendance': {'view': 'own_only', 'mark': False},
            'leave': {'view': 'own_only', 'approve': False},
            'payroll': {'view': 'own_only', 'edit': False, 'approve': False},
            'appraisals': {'view': 'own_only', 'create': False, 'review': False},
            'gamification': {'view': True, 'award': False, 'manage': False},
            'compliance': {'view': 'own_only', 'assign': False, 'manage': False},
            'forecasting': {'view': False, 'create': False},
            'attrition': {'view': False, 'record': False, 'analytics': False},
            'activity_logs': False,
            'user_management': False,
            'system_settings': False,
        }
    }

    return features.get(role_lower, features['employee'])


def get_user_employee_id(user_id: int, company_id: int) -> int:
    """Get the employee_id for a given user_id."""
    try:
        result = query(
            "SELECT id FROM employees_core WHERE user_id = %s AND company_id = %s",
            (user_id, company_id),
            one=True
        )
        return result['id'] if result else None
    except Exception as e:
        logger.error(f"Failed to get employee_id: {e}")
        return None


def get_user_department_id(user_id: int, company_id: int) -> int:
    """Get the department_id for a user (manager scope)."""
    try:
        result = query(
            "SELECT department_id FROM employees_core WHERE user_id = %s AND company_id = %s",
            (user_id, company_id),
            one=True
        )
        return result['department_id'] if result else None
    except Exception as e:
        logger.error(f"Failed to get department_id: {e}")
        return None


# ============================================================================
# SPECIALIZED DECORATORS
# ============================================================================

def allow_chro_except_settings(f):
    """
    CHRO can access everything EXCEPT /admin/settings routes.
    Used on sensitive admin endpoints.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()

        # Allow Admin only, deny CHRO
        if user_role == 'chro':
            flash('Access denied — CHRO cannot access system settings.', 'danger')
            return redirect(url_for('dashboard.index'))

        # Only allow Admin
        if user_role != 'admin':
            flash('Access denied — insufficient permissions.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper


def allow_hr_except_delete(f):
    """
    HR can access most features EXCEPT permanent employee deletion.
    Used on employee deletion endpoints.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()

        # Only Admin can delete permanently, not HR
        if user_role == 'hr':
            flash('Access denied — HR cannot permanently delete employees.', 'danger')
            return redirect(url_for('dashboard.index'))

        # Allow Admin only
        if user_role != 'admin':
            flash('Access denied — insufficient permissions.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper


def allow_manager_no_payroll(f):
    """
    Deny Manager access to payroll routes.
    Manager should NOT see any payroll data.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()

        # Deny Manager and Employee
        if user_role in ['manager', 'employee']:
            flash('Access denied — your role cannot access payroll.', 'danger')
            return redirect(url_for('dashboard.index'))

        # Allow Admin, HR, CHRO
        if user_role not in ['admin', 'hr', 'chro']:
            flash('Access denied — insufficient permissions.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper


def allow_employee_own_data_only(f):
    """
    Employee can only view/edit their OWN data.
    Validate that requested employee_id matches user's own employee_id.

    Expects: employee_id as URL parameter or form data.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request

        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()
        user_id = session.get('user_id')
        company_id = session.get('company_id')

        # Get requested employee_id from kwargs or form
        requested_employee_id = kwargs.get('employee_id') or request.form.get('employee_id')

        if requested_employee_id:
            requested_employee_id = int(requested_employee_id)
            user_employee_id = get_user_employee_id(user_id, company_id)

            # If Employee role, enforce ownership
            if user_role == 'employee' and user_employee_id != requested_employee_id:
                logger.warning(
                    f"Unauthorized access attempt: User {user_id} (emp {user_employee_id}) "
                    f"tried to access employee {requested_employee_id}"
                )
                flash('Access denied — you can only view your own data.', 'danger')
                return redirect(url_for('dashboard.index'))

            # If Manager, enforce department scope
            if user_role == 'manager':
                manager_emp = query(
                    "SELECT department_id FROM employees_core WHERE user_id = %s",
                    (user_id,),
                    one=True
                )
                if manager_emp:
                    requested_emp = query(
                        "SELECT department_id FROM employees_core WHERE id = %s",
                        (requested_employee_id,),
                        one=True
                    )
                    if not requested_emp or requested_emp['department_id'] != manager_emp['department_id']:
                        flash('Access denied — you can only manage your department.', 'danger')
                        return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper


def require_data_ownership(f):
    """
    Verify that user accessing a record owns or has permission to access it.
    More granular than allow_employee_own_data_only.

    Expects: employee_id or record_id as URL parameter.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request

        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_id = session.get('user_id')
        user_role = session.get('role', 'Employee').strip().lower()
        company_id = session.get('company_id')

        # Get employee_id from URL or request
        employee_id = kwargs.get('employee_id') or request.args.get('employee_id') or request.form.get('employee_id')
        record_id = kwargs.get('record_id') or request.args.get('record_id') or request.form.get('record_id')

        if not employee_id and not record_id:
            # No record specified, allow
            return f(*args, **kwargs)

        # Check ownership
        if employee_id:
            employee_id = int(employee_id)
            user_employee_id = get_user_employee_id(user_id, company_id)

            if user_role == 'employee' and user_employee_id != employee_id:
                logger.warning(f"Data ownership violation: User {user_id} vs Employee {employee_id}")
                return jsonify({'error': 'Access denied'}), 403

            if user_role == 'manager':
                user_dept = get_user_department_id(user_id, company_id)
                emp_dept = query(
                    "SELECT department_id FROM employees_core WHERE id = %s",
                    (employee_id,),
                    one=True
                )
                if emp_dept and emp_dept['department_id'] != user_dept:
                    logger.warning(f"Department scope violation: User {user_id} in dept {user_dept}")
                    return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)
    return wrapper


def deny_manager_from_payroll(f):
    """
    Explicit decorator to deny Manager access to any payroll endpoint.
    Returns JSON response for API endpoints.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()

        if user_role == 'manager':
            flash('Managers do not have access to payroll.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper


def deny_employee_editing(f):
    """
    Employee should NOT be able to edit any data, only view.
    Used on PATCH/PUT endpoints for employee-accessible routes.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        user_role = session.get('role', 'Employee').strip().lower()

        if user_role == 'employee':
            flash('Employees cannot edit this data.', 'danger')
            return redirect(url_for('dashboard.index'))

        return f(*args, **kwargs)
    return wrapper
