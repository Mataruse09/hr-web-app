from functools import wraps
from flask import session, redirect, url_for, flash
import os
import logging
import smtplib
from email.message import EmailMessage


def send_email(to_address: str, subject: str, body: str, html: str = None):
    smtp_host = os.getenv('SMTP_HOST') or os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER') or os.getenv('SMTP_EMAIL')
    smtp_pass = os.getenv('SMTP_PASS') or os.getenv('SMTP_PASSWORD')
    smtp_use_tls = os.getenv('SMTP_USE_TLS', 'True').strip().lower() in ('1', 'true', 'yes')
    smtp_use_ssl = os.getenv('SMTP_USE_SSL', 'False').strip().lower() in ('1', 'true', 'yes')

    if not smtp_host or not smtp_user or not smtp_pass:
        raise RuntimeError('SMTP configuration is missing: set SMTP_HOST, SMTP_USER, and SMTP_PASS (or SMTP_PASSWORD)')

    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = smtp_user
    message['To'] = to_address

    # ✅ FIX: support HTML emails for reset links
    if html:
        message.set_content(body)  # fallback text
        message.add_alternative(html, subtype='html')
    else:
        message.set_content(body)

    try:
        if smtp_use_ssl or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                if smtp_use_tls or smtp_port == 587:
                    server.starttls()
                    server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"SMTP send failed ({type(exc).__name__}): {exc}")


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Session expired. Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if company is still active (in case it was banned after login)
        company_id = session.get('company_id')
        if company_id:
            from models import company_model
            company = company_model.get_by_id_any_status(company_id)
            if company and not company.get('is_active', True):
                # Company has been deactivated/banned - log out all users
                session.clear()
                flash('Your company account has been suspended. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            if company and company.get('ban_reason'):
                session.clear()
                flash(f'Access denied: {company.get("ban_reason")}. Please contact support.', 'danger')
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
                # Only clear user-specific session data, preserve owner session
                user_keys = ['user_id', 'company_id', 'role', 'username', 'full_name', 'email']
                for key in user_keys:
                    session.pop(key, None)
                flash('Session expired. Please log in.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role', '').strip().lower()
            if user_role not in normalized:
                flash('Access denied — insufficient permissions.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator