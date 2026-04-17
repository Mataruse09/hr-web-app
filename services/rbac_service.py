"""
Role-Based Access Control (RBAC) Service
"""
from models.db import query, mutate
from functools import wraps
from flask import session, jsonify, redirect, url_for, flash
import logging

logger = logging.getLogger(__name__)

# Role hierarchy
ROLE_HIERARCHY = {
    'Admin': 999,
    'CHRO': 800,
    'Manager': 600,
    'HR': 700,
    'Employee': 100,
}


def has_permission(user_role: str, permission: str, company_id: int) -> bool:
    """Check if a role has a specific permission."""
    try:
        result = query("""
            SELECT id FROM permissions
            WHERE role = %s AND permission = %s
        """, (user_role, permission), one=True)
        return result is not None
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        return False


def get_user_permissions(company_id: int, user_id: int, role: str) -> list:
    """Get all permissions for a user based on their role."""
    try:
        permissions = query("""
            SELECT permission FROM permissions
            WHERE role = %s
        """, (role,))
        return [p['permission'] for p in permissions]
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        return []


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'danger')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role', 'Employee')
            company_id = session.get('company_id')
            
            if not has_permission(user_role, permission, company_id):
                flash('You do not have permission to access this feature.', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """Decorator to require one of multiple roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'danger')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role', 'Employee')
            
            if user_role not in allowed_roles:
                flash(f'This feature requires one of: {", ".join(allowed_roles)}', 'danger')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """Decorator to require Admin role."""
    return require_role('Admin')


def require_hr_or_above():
    """Decorator to require HR or Admin."""
    return require_role('Admin', 'HR', 'CHRO')


def can_view_employee_data(viewer_role: str, viewer_id: int, employee_id: int, company_id: int) -> bool:
    """Check if a user can view another employee's personal data."""
    try:
        # Admin can see everything
        if viewer_role == 'Admin':
            return True
        
        # HR, CHRO, Manager can see all employees' general data (not sensitive personal)
        if viewer_role in ['HR', 'CHRO', 'Manager']:
            return True
        
        # Employee can only see their own data
        if viewer_role == 'Employee':
            # Check if viewer is the employee
            viewer = query("""
                SELECT id FROM employees_core
                WHERE user_id = %s AND company_id = %s
            """, (viewer_id, company_id), one=True)
            
            if viewer and viewer['id'] == employee_id:
                return True
            return False
        
        return False
    except Exception as e:
        logger.error(f"Data access check failed: {e}")
        return False


def can_edit_employee_data(editor_role: str, company_id: int) -> bool:
    """Check if a user can edit employee data."""
    if editor_role == 'Admin':
        return True
    if editor_role in ['HR', 'CHRO']:
        return True
    return False


def can_approve_payroll(approver_role: str, company_id: int) -> bool:
    """Check if a user can approve payroll."""
    if approver_role == 'Admin':
        return True
    if approver_role in ['CHRO', 'HR']:
        return True
    return False


def can_manage_appraisals(user_role: str, company_id: int) -> bool:
    """Check if a user can manage appraisals."""
    if user_role == 'Admin':
        return True
    if user_role in ['HR', 'CHRO', 'Manager']:
        return True
    return False


def get_accessible_employees(user_id: int, user_role: str, company_id: int):
    """Get list of employees the user has access to view."""
    try:
        if user_role == 'Admin':
            # Admin sees all employees
            return query("""
                SELECT * FROM employees_core
                WHERE company_id = %s
                ORDER BY first_name, last_name
            """, (company_id,))
        
        elif user_role == 'Manager':
            # Manager sees employees in their department
            return query("""
                SELECT ec.* FROM employees_core ec
                WHERE ec.company_id = %s
                AND ec.department_id IN (
                    SELECT DISTINCT department_id FROM employees_core
                    WHERE user_id = %s
                )
                ORDER BY ec.first_name, ec.last_name
            """, (company_id, user_id))
        
        elif user_role == 'Employee':
            # Employee only sees themselves
            return query("""
                SELECT * FROM employees_core
                WHERE company_id = %s AND user_id = %s
            """, (company_id, user_id))
        
        else:  # HR, CHRO
            # HR/CHRO sees all employees
            return query("""
                SELECT * FROM employees_core
                WHERE company_id = %s
                ORDER BY first_name, last_name
            """, (company_id,))
    
    except Exception as e:
        logger.error(f"Failed to get accessible employees: {e}")
        return []
