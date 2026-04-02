from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    """Usage:  @roles_required('Admin', 'HR', 'company_admin', 'Manager', 'Employee', 'CHRO')"""
    normalized = {r.strip().lower() for r in allowed_roles}
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            user_role = session.get('role', '').strip().lower()
            if user_role not in normalized:
                flash('Access denied — insufficient permissions.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator