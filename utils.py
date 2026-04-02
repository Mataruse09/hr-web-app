from functools import wraps
from flask import session, redirect, url_for, flash
import os
import smtplib
from email.message import EmailMessage


def send_email(to_address: str, subject: str, body: str):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    if not smtp_host or not smtp_user or not smtp_pass:
        raise RuntimeError('SMTP configuration is missing')

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = smtp_user
    message['To'] = to_address
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(message)


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