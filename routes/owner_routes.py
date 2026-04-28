"""
Owner Routes - Private Super Admin Dashboard
Only accessible by the website owner - not company admins
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
import logging
from datetime import datetime, timedelta
import hashlib
import os
from dotenv import load_dotenv

# Load .env file to get environment variables
load_dotenv()

from models.db import query, mutate
from services.email_service import send_email

logger = logging.getLogger(__name__)

owner_bp = Blueprint('owner', __name__)

# Get secret key from environment variable (more secure)
# Set this in your environment: export OWNER_SECRET_KEY="your-very-secret-key"
OWNER_SECRET_KEY = os.environ.get('OWNER_SECRET_KEY', '642e50f116ad37511e895a9329983af5')

# Obfuscated route path - change this to something unique
OWNER_ROUTE_HASH = os.environ.get('OWNER_ROUTE_HASH', 'x7k9m2p4q8')

# Security: Track failed login attempts
failed_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 15  # minutes


# ═══════════════════════════════════════════════════════════════════════════
# EMAIL NOTIFICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def send_company_ban_email(company_id: int, reason: str):
    """Send email notification to company admin when banned."""
    try:
        # Get company and admin details
        company = query("""
            SELECT c.name, c.email, u.email as admin_email, u.full_name
            FROM companies c
            LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
            WHERE c.id = %s
        """, (company_id,), one=True)
        
        if not company or not company.get('admin_email'):
            logger.warning(f"No admin email found for company {company_id}")
            return False
        
        subject = f"⚠️ Important: Your MatinexHR Account Has Been Suspended"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">🚫 Account Suspended</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <p>Dear <strong>{company.get('full_name', 'Administrator')}</strong>,</p>
                
                <p>We regret to inform you that your organization's access to <strong>MatinexHR</strong> has been <strong>suspended</strong>.</p>
                
                <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #991b1b;">Reason for Suspension:</h4>
                    <p style="margin-bottom: 0;">{reason}</p>
                </div>
                
                <p>If you believe this action was taken in error or would like to discuss this matter, please contact our support team immediately.</p>
                
                <p>We encourage you to resolve any concerns promptly so we can restore your service.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px;">
                        Best regards,<br>
                        <strong>MatinexHR Support Team</strong><br>
                        support@matinexhr.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(company['admin_email'], subject, body, is_html=True)
    except Exception as e:
        logger.error(f"Failed to send ban email: {e}")
        return False


def send_company_unban_email(company_id: int):
    """Send email notification to company admin when unbanned."""
    try:
        company = query("""
            SELECT c.name, u.email as admin_email, u.full_name
            FROM companies c
            LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
            WHERE c.id = %s
        """, (company_id,), one=True)
        
        if not company or not company.get('admin_email'):
            return False
        
        subject = f"✅ Good News: Your MatinexHR Account Has Been Restored"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">✅ Account Restored</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <p>Dear <strong>{company.get('full_name', 'Administrator')}</strong>,</p>
                
                <p>We are pleased to inform you that your organization's access to <strong>MatinexHR</strong> has been <strong>restored</strong>.</p>
                
                <p>You can now log in to your dashboard and continue using our services.</p>
                
                <div style="background: #ecfdf5; border-left: 4px solid #059669; padding: 15px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #047857;">Next Steps:</h4>
                    <ul style="margin-bottom: 0;">
                        <li>Log in to your admin dashboard</li>
                        <li>Verify all features are working correctly</li>
                        <li>Contact support if you experience any issues</li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px;">
                        Thank you for your patience,<br>
                        <strong>MatinexHR Support Team</strong><br>
                        support@matinexhr.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(company['admin_email'], subject, body, is_html=True)
    except Exception as e:
        logger.error(f"Failed to send unban email: {e}")
        return False


def send_subscription_change_email(company_id: int, change_type: str, details: str):
    """Send email notification to company admin about subscription changes."""
    try:
        company = query("""
            SELECT c.name, u.email as admin_email, u.full_name
            FROM companies c
            LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
            WHERE c.id = %s
        """, (company_id,), one=True)
        
        if not company or not company.get('admin_email'):
            return False
        
        if change_type == 'price_increase':
            subject = f"📢 Subscription Price Update - MatinexHR"
            color = "#ea580c"
            icon = "📢"
        elif change_type == 'price_decrease':
            subject = f"💰 Subscription Price Update - MatinexHR"
            color = "#059669"
            icon = "💰"
        elif change_type == 'free_access':
            subject = f"🎉 Free Access Granted - MatinexHR"
            color = "#7c3aed"
            icon = "🎉"
        else:
            subject = f"📋 Subscription Update - MatinexHR"
            color = "#2563eb"
            icon = "📋"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">{icon} Subscription Update</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <p>Dear <strong>{company.get('full_name', 'Administrator')}</strong>,</p>
                
                <p>We want to inform you about a change to your <strong>MatinexHR</strong> subscription:</p>
                
                <div style="background: #f9fafb; padding: 15px; margin: 20px 0; border-radius: 8px;">
                    <p style="margin-bottom: 0; font-size: 16px;">{details}</p>
                </div>
                
                <p>If you have any questions about this change, please don't hesitate to contact our support team.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px;">
                        Best regards,<br>
                        <strong>MatinexHR Support Team</strong><br>
                        support@matinexhr.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(company['admin_email'], subject, body, is_html=True)
    except Exception as e:
        logger.error(f"Failed to send subscription change email: {e}")
        return False


def send_custom_email_to_company(company_id: int, subject: str, message: str):
    """Send a custom formal email to company admin."""
    try:
        company = query("""
            SELECT c.name, u.email as admin_email, u.full_name
            FROM companies c
            LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
            WHERE c.id = %s
        """, (company_id,), one=True)
        
        if not company or not company.get('admin_email'):
            return False
        
        full_subject = f"📬 {subject}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">📬 Message from MatinexHR</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e5e7eb; border-top: none;">
                <p>Dear <strong>{company.get('full_name', 'Administrator')}</strong>,</p>
                
                <div style="background: #f9fafb; padding: 20px; margin: 20px 0; border-radius: 8px; line-height: 1.6;">
                    {message}
                </div>
                
                <p>We value your partnership and are here to support you.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px;">
                        Best regards,<br>
                        <strong>MatinexHR Administration</strong><br>
                        support@matinexhr.com
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(company['admin_email'], full_subject, body, is_html=True)
    except Exception as e:
        logger.error(f"Failed to send custom email: {e}")
        return False


def is_owner_logged_in():
    """Check if owner is logged in via session"""
    return session.get('is_owner') == True


def require_owner(f):
    """Decorator to require owner authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_owner_logged_in():
            return redirect(url_for('owner.login', _external=False))
        return f(*args, **kwargs)
    return decorated_function


# Use obfuscated route path
@owner_bp.route(f'/{OWNER_ROUTE_HASH}')
def index():
    """Redirect root owner path to login"""
    return redirect(url_for('owner.login'))

@owner_bp.route(f'/{OWNER_ROUTE_HASH}/login', methods=['GET', 'POST'])
def login():
    """Owner login page - secret route"""
    # Check for too many failed attempts
    ip = request.remote_addr
    if ip in failed_attempts:
        attempts, last_attempt = failed_attempts[ip]
        if attempts >= MAX_LOGIN_ATTEMPTS:
            # Check if lockout has expired
            if datetime.utcnow() - last_attempt < timedelta(minutes=LOCKOUT_DURATION):
                minutes_left = LOCKOUT_DURATION - (datetime.utcnow() - last_attempt).seconds // 60
                return render_template('owner/login.html', 
                                      error=f"Too many failed attempts. Try again in {minutes_left} minutes.",
                                      locked=True)
            else:
                # Lockout expired
                failed_attempts[ip] = (0, datetime.utcnow())
    
    if request.method == 'POST':
        secret_key = request.form.get('secret_key', '').strip()
        
        if secret_key == OWNER_SECRET_KEY:
            # Successful login
            session['is_owner'] = True
            session.permanent = True
            # Clear failed attempts
            if ip in failed_attempts:
                del failed_attempts[ip]
            logger.info(f"Owner logged in from IP: {ip}")
            return redirect(url_for('owner.dashboard'))
        else:
            # Failed attempt
            if ip in failed_attempts:
                attempts, _ = failed_attempts[ip]
                failed_attempts[ip] = (attempts + 1, datetime.utcnow())
            else:
                failed_attempts[ip] = (1, datetime.utcnow())
            
            attempts_left = MAX_LOGIN_ATTEMPTS - failed_attempts.get(ip, (0, datetime.utcnow()))[0]
            logger.warning(f"Failed owner login attempt from IP: {ip}")
            return render_template('owner/login.html', 
                                  error=f"Invalid secret key. {attempts_left} attempts remaining.")
    
    return render_template('owner/login.html')


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/logout')
def logout():
    """Owner logout - only clear owner session, not regular user session"""
    # Only clear owner-specific session data, preserve regular user session
    session.pop('is_owner', None)
    session.permanent = False
    return redirect(url_for('owner.login'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/dashboard')
@require_owner
def dashboard():
    """Owner dashboard - overview of entire platform"""
    try:
        # Get platform statistics
        stats = {}
        
        # Total companies
        result = query("SELECT COUNT(*) as count FROM companies", one=True)
        stats['total_companies'] = result['count'] if result else 0
        
        # Active companies
        result = query("SELECT COUNT(*) as count FROM companies WHERE is_active = TRUE", one=True)
        stats['active_companies'] = result['count'] if result else 0
        
        # Banned companies - use is_banned column if it exists, otherwise use ban_reason
        try:
            result = query("SELECT COUNT(*) as count FROM companies WHERE is_banned = TRUE", one=True)
            stats['banned_companies'] = result['count'] if result else 0
        except:
            # Fallback: check companies with ban_reason but no is_banned column
            try:
                result = query("SELECT COUNT(*) as count FROM companies WHERE ban_reason IS NOT NULL AND ban_reason != ''", one=True)
                stats['banned_companies'] = result['count'] if result else 0
            except:
                stats['banned_companies'] = 0
        
        # Total users
        result = query("SELECT COUNT(*) as count FROM users", one=True)
        stats['total_users'] = result['count'] if result else 0
        
        # Total employees (use employees_core table)
        try:
            result = query("SELECT COUNT(*) as count FROM employees_core", one=True)
            stats['total_employees'] = result['count'] if result else 0
        except:
            stats['total_employees'] = 0
        
        # Recent abuse reports (table may not exist)
        try:
            recent_reports = query("""
                SELECT ar.*, c.name as company_name 
                FROM abuse_reports ar
                JOIN companies c ON ar.company_id = c.id
                ORDER BY ar.created_at DESC
                LIMIT 10
            """)
        except:
            recent_reports = []
        
        # Recent companies (use employees_core table)
        try:
            recent_companies = query("""
                SELECT c.*, 
                       (SELECT COUNT(*) FROM users WHERE company_id = c.id) as user_count,
                       (SELECT COUNT(*) FROM employees_core WHERE company_id = c.id) as employee_count
                FROM companies c
                ORDER BY c.created_at DESC
                LIMIT 10
            """)
        except:
            recent_companies = []
        
        # Security events - use existing activity_logs table (all companies)
        try:
            security_events = query("""
                SELECT al.*, c.name as company_name
                FROM activity_logs al
                LEFT JOIN companies c ON al.company_id = c.id
                WHERE al.created_at > NOW() - INTERVAL 24 HOUR
                AND (al.action LIKE '%login%' OR al.action LIKE '%failed%' OR al.action LIKE '%LOGIN%')
                ORDER BY al.created_at DESC
                LIMIT 20
            """)
        except:
            security_events = []
        
        return render_template('owner/dashboard.html',
                              stats=stats,
                              recent_reports=recent_reports,
                              recent_companies=recent_companies,
                              security_events=security_events)
    except Exception as e:
        logger.exception(e)
        flash('Error loading dashboard.', 'danger')
        return render_template('owner/dashboard.html',
                              stats={'total_companies': 0, 'active_companies': 0, 'banned_companies': 0, 'total_users': 0, 'total_employees': 0},
                              recent_reports=[],
                              recent_companies=[],
                              security_events=[])


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/companies')
@require_owner
def all_companies():
    """View all companies - owner only"""
    try:
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        query_str = """
            SELECT c.*, 
                   (SELECT COUNT(*) FROM users WHERE company_id = c.id) as user_count,
                   (SELECT COUNT(*) FROM employees_core WHERE company_id = c.id) as employee_count
            FROM companies c
            WHERE 1=1
        """
        params = []
        
        if search:
            query_str += " AND (c.name LIKE %s OR c.email LIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        if status_filter == 'active':
            query_str += " AND c.is_active = TRUE"
        elif status_filter == 'inactive':
            query_str += " AND c.is_active = FALSE"
        elif status_filter == 'banned':
            # Try to filter by is_banned column, fallback to ban_reason
            try:
                query_str += " AND c.is_banned = TRUE"
            except:
                query_str += " AND c.ban_reason IS NOT NULL AND c.ban_reason != ''"
        
        query_str += " ORDER BY c.created_at DESC"
        
        companies = query(query_str, tuple(params) if params else None)
        
        return render_template('owner/companies.html', companies=companies, search=search, status_filter=status_filter)
    except Exception as e:
        logger.exception(e)
        flash('Error loading companies.', 'danger')
        return redirect(url_for('owner.dashboard'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/companies/<int:company_id>/view')
@require_owner
def view_company(company_id):
    """View company details - owner only"""
    try:
        company = query("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM users WHERE company_id = c.id) as user_count,
                   (SELECT COUNT(*) FROM employees_core WHERE company_id = c.id) as employee_count
            FROM companies c
            WHERE c.id = %s
        """, (company_id,), one=True)
        
        if not company:
            flash('Company not found.', 'warning')
            return redirect(url_for('owner.all_companies'))
        
        # Get company users
        users = query("""
            SELECT id, username, email, full_name, role, is_active, created_at
            FROM users WHERE company_id = %s
            ORDER BY created_at DESC
        """, (company_id,))
        
        # Get company employees
        try:
            employees = query("""
                SELECT id, employee_code, first_name, last_name, email, department_id, job_title, is_active
                FROM employees_core WHERE company_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (company_id,))
        except:
            employees = []
        
        # Get abuse reports for this company (table may not exist)
        try:
            abuse_reports = query("""
                SELECT * FROM abuse_reports 
                WHERE company_id = %s
                ORDER BY created_at DESC
            """, (company_id,))
        except:
            abuse_reports = []
        
        return render_template('owner/company_view.html',
                              company=company,
                              users=users,
                              employees=employees,
                              abuse_reports=abuse_reports)
    except Exception as e:
        logger.exception(e)
        flash('Error loading company.', 'danger')
        return redirect(url_for('owner.all_companies'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/companies/<int:company_id>/ban', methods=['POST'])
@require_owner
def ban_company(company_id):
    """Ban a company - owner only"""
    reason = request.form.get('reason', '').strip()
    ban_type = request.form.get('ban_type', 'manual')
    send_email_notification = request.form.get('send_email', 'on') == 'on'
    
    if not reason:
        flash('Ban reason is required.', 'warning')
        return redirect(url_for('owner.view_company', company_id=company_id))
    
    try:
        # Try to update with is_banned column, fallback if doesn't exist
        try:
            mutate("""
                UPDATE companies 
                SET is_banned = TRUE, ban_reason = %s, banned_at = %s, banned_by = NULL, 
                    ban_type = %s, is_active = FALSE
                WHERE id = %s
            """, (reason, datetime.utcnow(), ban_type, company_id))
        except:
            mutate("""
                UPDATE companies 
                SET ban_reason = %s, banned_at = %s, banned_by = NULL, 
                    ban_type = %s, is_active = FALSE
                WHERE id = %s
            """, (reason, datetime.utcnow(), ban_type, company_id))
        
        # Log the ban (table may not exist)
        try:
            mutate("""
                INSERT INTO activity_logs (company_id, user_id, action, details) 
                VALUES (NULL, NULL, %s, %s)
            """, (f'company_banned_{company_id}', f'Company {company_id} banned: {reason}'))
        except:
            pass
        
        # Send email notification to company admin
        if send_email_notification:
            send_company_ban_email(company_id, reason)
        
        flash(f'Company has been banned.{" Email notification sent." if send_email_notification else ""}', 'success')
        logger.warning(f"Owner banned company {company_id}: {reason}")
    except Exception as e:
        logger.exception(e)
        flash('Error banning company.', 'danger')
    
    return redirect(url_for('owner.view_company', company_id=company_id))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/companies/<int:company_id>/unban', methods=['POST'])
@require_owner
def unban_company(company_id):
    """Unban a company - owner only"""
    send_email_notification = request.form.get('send_email', 'on') == 'on'
    
    try:
        # Try to update with is_banned column, fallback if doesn't exist
        try:
            mutate("""
                UPDATE companies 
                SET is_banned = FALSE, ban_reason = NULL, banned_at = NULL, banned_by = NULL, 
                    ban_type = 'manual', auto_ban_trigger = NULL, is_active = TRUE
                WHERE id = %s
            """, (company_id,))
        except:
            mutate("""
                UPDATE companies 
                SET ban_reason = NULL, banned_at = NULL, banned_by = NULL, 
                    ban_type = 'manual', auto_ban_trigger = NULL, is_active = TRUE
                WHERE id = %s
            """, (company_id,))
        
        # Log the unban (table may not exist)
        try:
            mutate("""
                INSERT INTO activity_logs (company_id, user_id, action, details) 
                VALUES (NULL, NULL, %s, %s)
            """, (f'company_unbanned_{company_id}', f'Company {company_id} unbanned by owner'))
        except:
            pass
        
        # Send email notification to company admin
        if send_email_notification:
            send_company_unban_email(company_id)
        
        flash(f'Company has been unbanned and reactivated.{" Email notification sent." if send_email_notification else ""}', 'success')
        logger.info(f"Owner unbanned company {company_id}")
    except Exception as e:
        logger.exception(e)
        flash('Error unbanning company.', 'danger')
    
    return redirect(url_for('owner.view_company', company_id=company_id))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/companies/<int:company_id>/delete', methods=['POST'])
@require_owner
def delete_company(company_id):
    """Permanently delete a company and all its data - owner only"""
    confirm_text = request.form.get('confirm_delete', '').strip()
    
    if confirm_text != 'DELETE':
        flash('Type DELETE to confirm.', 'warning')
        return redirect(url_for('owner.view_company', company_id=company_id))
    
    try:
        company_name = query("SELECT name FROM companies WHERE id = %s", (company_id,), one=True)
        
        # Delete in correct order (use employees_core, handle missing tables)
        try:
            mutate("DELETE FROM attendance_logs WHERE company_id = %s", (company_id,))
        except:
            pass
        try:
            mutate("DELETE FROM leave_requests WHERE company_id = %s", (company_id,))
        except:
            pass
        try:
            mutate("DELETE FROM employees_core WHERE company_id = %s", (company_id,))
        except:
            pass
        try:
            mutate("DELETE FROM users WHERE company_id = %s", (company_id,))
        except:
            pass
        try:
            mutate("DELETE FROM abuse_reports WHERE company_id = %s", (company_id,))
        except:
            pass
        mutate("DELETE FROM companies WHERE id = %s", (company_id,))
        
        flash(f'Company "{company_name["name"]}" and all its data has been permanently deleted.', 'success')
        logger.critical(f"Owner permanently deleted company {company_id}: {company_name['name']}")
    except Exception as e:
        logger.exception(e)
        flash('Error deleting company.', 'danger')
    
    return redirect(url_for('owner.all_companies'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/abuse-reports')
@require_owner
def abuse_reports():
    """View all abuse reports - owner only"""
    try:
        status_filter = request.args.get('status', '')
        severity_filter = request.args.get('severity', '')
        
        # Try to query abuse_reports table (may not exist)
        try:
            query_str = """
                SELECT ar.*, c.name as company_name 
                FROM abuse_reports ar
                JOIN companies c ON ar.company_id = c.id
                WHERE 1=1
            """
            params = []
            
            if status_filter:
                query_str += " AND ar.status = %s"
                params.append(status_filter)
            
            if severity_filter:
                query_str += " AND ar.severity = %s"
                params.append(severity_filter)
            
            query_str += " ORDER BY ar.created_at DESC"
            
            reports = query(query_str, tuple(params) if params else None)
        except:
            reports = []
        
        return render_template('owner/abuse_reports.html', reports=reports, 
                             status_filter=status_filter, severity_filter=severity_filter)
    except Exception as e:
        logger.exception(e)
        flash('Error loading reports.', 'danger')
        return redirect(url_for('owner.dashboard'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/abuse-reports/<int:report_id>/resolve', methods=['POST'])
@require_owner
def resolve_abuse_report(report_id):
    """Resolve an abuse report - owner only"""
    status = request.form.get('status', 'resolved')
    resolution_notes = request.form.get('resolution_notes', '').strip()
    action = request.form.get('action', '')  # 'ban_company' to ban the company
    
    try:
        # Try to update abuse_reports table (may not exist)
        try:
            mutate("""
                UPDATE abuse_reports 
                SET status = %s, resolved_by = NULL, resolution_notes = %s, resolved_at = %s, updated_at = %s
                WHERE id = %s
            """, (status, resolution_notes, datetime.utcnow(), datetime.utcnow(), report_id))
        except:
            pass
        
        # If action is to ban company
        if action == 'ban_company':
            company_id = request.form.get('company_id', type=int)
            if company_id:
                # Try to update with is_banned column, fallback if doesn't exist
                try:
                    mutate("""
                        UPDATE companies 
                        SET is_banned = TRUE, ban_reason = %s, banned_at = %s, ban_type = 'manual'
                        WHERE id = %s
                    """, (f"Auto-banned from abuse report #{report_id}: {resolution_notes}", datetime.utcnow(), company_id))
                except:
                    mutate("""
                        UPDATE companies 
                        SET ban_reason = %s, banned_at = %s, ban_type = 'manual', is_active = FALSE
                        WHERE id = %s
                    """, (f"Auto-banned from abuse report #{report_id}: {resolution_notes}", datetime.utcnow(), company_id))
        
        flash('Report updated.', 'success')
    except Exception as e:
        logger.exception(e)
        flash('Error updating report.', 'danger')
    
    return redirect(url_for('owner.abuse_reports'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/security')
@require_owner
def security():
    """Security dashboard - owner only"""
    try:
        # Get security statistics
        stats = {}
        
        # Failed logins (last 24 hours) - use existing activity_logs table
        try:
            result = query("""
                SELECT COUNT(*) as count FROM activity_logs 
                WHERE created_at > NOW() - INTERVAL 24 HOUR
                AND (action LIKE '%failed%' OR action LIKE '%FAILED%')
            """, one=True)
            stats['failed_logins_24h'] = result['count'] if result else 0
        except:
            stats['failed_logins_24h'] = 0
        
        # Unique IPs with failed logins
        try:
            result = query("""
                SELECT COUNT(DISTINCT ip_address) as count FROM activity_logs 
                WHERE created_at > NOW() - INTERVAL 24 HOUR
                AND (action LIKE '%failed%' OR action LIKE '%FAILED%')
            """, one=True)
            stats['suspicious_ips'] = result['count'] if result else 0
        except:
            stats['suspicious_ips'] = 0
        
        # Banned companies (use is_active = FALSE as proxy)
        result = query("SELECT COUNT(*) as count FROM companies WHERE is_active = FALSE", one=True)
        stats['banned_companies'] = result['count'] if result else 0
        
        # Recent suspicious activity - use existing activity_logs table
        try:
            suspicious_activity = query("""
                SELECT al.*, c.name as company_name
                FROM activity_logs al
                LEFT JOIN companies c ON al.company_id = c.id
                WHERE al.created_at > NOW() - INTERVAL 24 HOUR
                AND (al.action LIKE '%failed%' OR al.action LIKE '%FAILED%' OR al.action LIKE '%error%')
                ORDER BY al.created_at DESC
                LIMIT 50
            """)
        except:
            suspicious_activity = []
        
        # Top suspicious IPs
        try:
            suspicious_ips = query("""
                SELECT ip_address, COUNT(*) as attempts, MAX(created_at) as last_attempt
                FROM activity_logs 
                WHERE created_at > NOW() - INTERVAL 24 HOUR
                AND (action LIKE '%failed%' OR action LIKE '%FAILED%')
                GROUP BY ip_address
                ORDER BY attempts DESC
                LIMIT 10
            """)
        except:
            suspicious_ips = []
        
        return render_template('owner/security.html',
                              stats=stats,
                              suspicious_activity=suspicious_activity,
                              suspicious_ips=suspicious_ips)
    except Exception as e:
        logger.exception(e)
        flash('Error loading security data.', 'danger')
        return redirect(url_for('owner.dashboard'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/security/block-ip', methods=['POST'])
@require_owner
def block_ip():
    """Block an IP address - owner only"""
    ip_address = request.form.get('ip_address', '').strip()
    reason = request.form.get('reason', '').strip()
    
    if not ip_address or not reason:
        flash('IP address and reason are required.', 'warning')
        return redirect(url_for('owner.security'))
    
    try:
        # Add to blocked IPs (MySQL syntax - use INSERT IGNORE and UPDATE)
        # First try to insert, if duplicate then update
        try:
            mutate("""
                INSERT INTO blocked_ips (ip_address, reason, blocked_by, is_active) 
                VALUES (%s, %s, 'owner', 1)
            """, (ip_address, reason))
        except:
            # If duplicate, update the existing record
            mutate("""
                UPDATE blocked_ips SET reason = %s, blocked_at = NOW(), is_active = 1 
                WHERE ip_address = %s
            """, (reason, ip_address))
        
        flash(f'IP {ip_address} has been blocked.', 'success')
        logger.warning(f"Owner blocked IP: {ip_address} - {reason}")
    except Exception as e:
        logger.exception(e)
        flash('Error blocking IP.', 'danger')
    
    return redirect(url_for('owner.security'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/logs')
@require_owner
def activity_logs():
    """View all activity logs - owner only"""
    try:
        action_filter = request.args.get('action', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        query_str = """
            SELECT al.*, c.name as company_name, u.username
            FROM activity_logs al
            LEFT JOIN companies c ON al.company_id = c.id
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if action_filter:
            query_str += " AND al.action LIKE %s"
            params.append(f"%{action_filter}%")
        
        if date_from:
            query_str += " AND al.created_at >= %s"
            params.append(date_from)
        
        if date_to:
            query_str += " AND al.created_at <= %s"
            params.append(date_to + ' 23:59:59')
        
        query_str += " ORDER BY al.created_at DESC LIMIT 200"
        
        logs = query(query_str, tuple(params) if params else None)
        
        return render_template('owner/logs.html', logs=logs, action_filter=action_filter)
    except Exception as e:
        logger.exception(e)
        flash('Error loading logs.', 'danger')
        return redirect(url_for('owner.dashboard'))


def check_and_notify_expiring_subscriptions():
    """Check for subscriptions expiring soon and send email notifications."""
    try:
        # Find subscriptions expiring in next 7 days
        expiring_subs = query("""
            SELECT cs.id, cs.company_id, cs.end_date, c.name as company_name, u.email as admin_email
            FROM company_subscriptions cs
            JOIN companies c ON cs.company_id = c.id
            LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
            WHERE cs.status = 'active' 
            AND cs.end_date IS NOT NULL 
            AND cs.end_date <= DATE_ADD(NOW(), INTERVAL 7 DAY)
            AND cs.end_date > NOW()
        """)
        
        count = 0
        for sub in expiring_subs:
            if sub and sub.get('admin_email'):
                days_left = (sub['end_date'] - datetime.utcnow()).days
                
                # Send reminder email
                send_subscription_change_email(
                    sub['company_id'], 'expiry_reminder',
                    f'⏰ Reminder: Your MatinexHR subscription expires in {days_left} days '
                    f'on {sub["end_date"].strftime("%B %d, %Y")}. '
                    'Please renew to continue using all features.'
                )
                count += 1
        
        logger.info(f"Expiry check: {count} companies notified")
        return count
    except Exception as e:
        logger.error(f"Error checking expiring subscriptions: {e}")
        return 0


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/settings', methods=['GET', 'POST'])
@require_owner
def settings():
    """Owner settings - change secret key"""
    if request.method == 'POST':
        new_key = request.form.get('new_secret_key', '').strip()
        confirm_key = request.form.get('confirm_secret_key', '').strip()
        
        if len(new_key) < 16:
            flash('Secret key must be at least 16 characters.', 'warning')
            return redirect(url_for('owner.settings'))
        
        if new_key != confirm_key:
            flash('Keys do not match.', 'warning')
            return redirect(url_for('owner.settings'))
        
        # In production, store this in a secure config
        flash('Settings updated. Note: Key change will take effect after restart.', 'success')
    
    return render_template('owner/settings.html')


# ═══════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION MANAGEMENT ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@owner_bp.route(f'/{OWNER_ROUTE_HASH}/subscriptions', methods=['GET', 'POST'])
@require_owner
def manage_subscriptions():
    """Manage subscription plans - owner only"""
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            # ============================================
            # GLOBAL FREE ACCESS - Set all to FREE (price = 0)
            # ============================================
            if action == 'set_global_free':
                """Set ALL companies to free access"""
                try:
                    # Update all active subscriptions to free
                    mutate("""
                        UPDATE company_subscriptions 
                        SET custom_price = 0, 
                            auto_renew = TRUE, 
                            updated_at = %s,
                            is_global_free = TRUE
                        WHERE status IN ('active', 'trial')
                    """, (datetime.utcnow(),))
                    
                    # Get all companies and notify them
                    companies = query("""
                        SELECT c.id, c.name, u.email as admin_email
                        FROM companies c
                        LEFT JOIN users u ON u.company_id = c.id AND u.role = 'admin'
                        WHERE c.is_active = TRUE
                    """)
                    
                    # Send bulk email notification
                    for company in companies:
                        if company and company.get('admin_email'):
                            send_subscription_change_email(
                                company['id'], 'free_access',
                                '🎉 Great news! All companies now have FREE access to MatinexHR! '
                                'All premium features are unlocked for you.'
                            )
                    
                    flash('✅ Global free access enabled! All companies now have free access.', 'success')
                    logger.info("Owner enabled global free access for all companies")
                except Exception as e:
                    logger.exception(e)
                    flash('Error enabling global free access.', 'danger')
            
            # ============================================
            # REMOVE GLOBAL FREE - Restore normal pricing
            # ============================================
            elif action == 'remove_global_free':
                """Remove global free access"""
                try:
                    # Remove global free flag and custom prices
                    mutate("""
                        UPDATE company_subscriptions 
                        SET is_global_free = FALSE, 
                            custom_price = NULL, 
                            updated_at = %s
                        WHERE is_global_free = TRUE
                    """, (datetime.utcnow(),))
                    
                    flash('✅ Global free access removed. Companies will now pay standard prices.', 'success')
                    logger.info("Owner removed global free access")
                except Exception as e:
                    logger.exception(e)
                    flash('Error removing global free access.', 'danger')
            
            # ============================================
            # GRANT FREE ACCESS TO SPECIFIC COMPANY
            # ============================================
            elif action == 'grant_free_access':
                company_id = request.form.get('company_id', type=int)
                duration_days = request.form.get('duration_days', type=int, default=30)
                
                if company_id and duration_days:
                    end_date = datetime.utcnow() + timedelta(days=duration_days)
                    
                    # Check if subscription exists
                    sub = query("""
                        SELECT id, custom_price FROM company_subscriptions 
                        WHERE company_id = %s AND status IN ('active', 'trial')
                        ORDER BY created_at DESC LIMIT 1
                    """, (company_id,), one=True)
                    
                    if sub:
                        # Update existing subscription to free
                        mutate("""
                            UPDATE company_subscriptions 
                            SET status = 'active', 
                                end_date = %s, 
                                custom_price = 0,
                                is_global_free = FALSE,
                                auto_renew = TRUE, 
                                updated_at = %s,
                                free_access_until = %s
                            WHERE id = %s
                        """, (end_date, datetime.utcnow(), end_date, sub['id']))
                    else:
                        # Create new free subscription
                        mutate("""
                            INSERT INTO company_subscriptions 
                            (company_id, plan_id, status, start_date, end_date, custom_price, auto_renew, free_access_until)
                            VALUES (%s, 1, 'active', %s, %s, 0, TRUE, %s)
                        """, (company_id, datetime.utcnow(), end_date, end_date))
                    
                    # Get company details for email
                    company = query("SELECT name FROM companies WHERE id = %s", (company_id,), one=True)
                    company_name = company['name'] if company else 'Your company'
                    
                    # Send email notification
                    send_subscription_change_email(
                        company_id, 'free_access',
                        f'🎉 Free Access Granted! Your company "{company_name}" now has FREE access '
                        f'for {duration_days} days (until {end_date.strftime("%B %d, %Y")}). '
                        'All premium features are unlocked!'
                    )
                    
                    flash(f'✅ Free access granted to company for {duration_days} days.', 'success')
                    logger.info(f"Owner granted free access to company {company_id} for {duration_days} days")
            
            # ============================================
            # REVOKE FREE ACCESS FROM COMPANY
            # ============================================
            elif action == 'revoke_free_access':
                company_id = request.form.get('company_id', type=int)
                
                if company_id:
                    # Remove free access
                    mutate("""
                        UPDATE company_subscriptions 
                        SET custom_price = NULL, 
                            auto_renew = TRUE, 
                            updated_at = %s,
                            free_access_until = NULL
                        WHERE company_id = %s AND status IN ('active', 'trial')
                    """, (datetime.utcnow(), company_id))
                    
                    # Get company details for email
                    company = query("SELECT name FROM companies WHERE id = %s", (company_id,), one=True)
                    company_name = company['name'] if company else 'Your company'
                    
                    send_subscription_change_email(
                        company_id, 'free_access',
                        f'Your free access for "{company_name}" has been revoked. '
                        'Your subscription will continue with standard pricing.'
                    )
                    
                    flash('✅ Free access revoked from company.', 'success')
                    logger.info(f"Owner revoked free access from company {company_id}")
            
            # ============================================
            # SET CUSTOM PRICE FOR COMPANY
            # ============================================
            elif action == 'set_custom_price':
                company_id = request.form.get('company_id', type=int)
                custom_price = request.form.get('custom_price', type=float)
                
                if company_id and custom_price is not None:
                    # Update company's subscription price
                    mutate("""
                        UPDATE company_subscriptions 
                        SET custom_price = %s, 
                            updated_at = %s,
                            free_access_until = NULL,
                            is_global_free = FALSE
                        WHERE company_id = %s AND status IN ('active', 'trial')
                    """, (custom_price, datetime.utcnow(), company_id))
                    
                    # Get company details for email
                    company = query("SELECT name FROM companies WHERE id = %s", (company_id,), one=True)
                    company_name = company['name'] if company else 'Your company'
                    
                    # Send email notification
                    if custom_price == 0:
                        send_subscription_change_email(
                            company_id, 'free_access',
                            f'Your subscription price for "{company_name}" has been set to $0.00/month. '
                            'You now have free access!'
                        )
                    else:
                        send_subscription_change_email(
                            company_id, 'price_increase',
                            f'Your subscription price for "{company_name}" has been updated to '
                            f'${custom_price:.2f}/month.'
                        )
                    
                    flash(f'✅ Custom price ${custom_price:.2f} set for company.', 'success')
                    logger.info(f"Owner set custom price ${custom_price} for company {company_id}")
            
            # ============================================
            # UPDATE PLAN PRICES
            # ============================================
            elif action == 'update_plan_price':
                plan_id = request.form.get('plan_id', type=int)
                price_monthly = request.form.get('price_monthly', type=float)
                price_yearly = request.form.get('price_yearly', type=float)
                
                if plan_id and price_monthly is not None and price_yearly is not None:
                    mutate("""
                        UPDATE subscription_plans 
                        SET price_monthly = %s, price_yearly = %s, updated_at = %s 
                        WHERE id = %s
                    """, (price_monthly, price_yearly, datetime.utcnow(), plan_id))
                    
                    flash(f'✅ Plan prices updated.', 'success')
            
            # ============================================
            # CHECK EXPIRING SUBSCRIPTIONS & SEND ALERTS
            # ============================================
            elif action == 'check_expiring':
                """Manually trigger expiry check"""
                try:
                    expiring = check_and_notify_expiring_subscriptions()
                    flash(f'✅ Checked subscriptions. {expiring} companies notified.', 'success')
                except Exception as e:
                    logger.exception(e)
                    flash('Error checking subscriptions.', 'danger')
        
        # Get all subscription plans
        plans = query("SELECT * FROM subscription_plans ORDER BY price_monthly")
        
        # Check if global free is enabled - handle missing column gracefully
        try:
            global_free = query("""
                SELECT COUNT(*) as count FROM company_subscriptions 
                WHERE is_global_free = TRUE AND status IN ('active', 'trial')
            """, one=True)
            is_global_free = global_free['count'] > 0 if global_free else False
        except:
            is_global_free = False
        
        # Get all companies with their subscriptions - handle missing columns gracefully
        try:
            companies = query("""
                SELECT c.id, c.name, c.email, c.is_active,
                       cs.status as sub_status, 
                       COALESCE(cs.custom_price, sp.price_monthly) as custom_price, 
                       cs.end_date,
                       cs.is_global_free,
                       cs.free_access_until,
                       sp.name as plan_name, 
                       sp.price_monthly as plan_price
                FROM companies c
                LEFT JOIN company_subscriptions cs ON cs.company_id = c.id AND cs.status IN ('active', 'trial')
                LEFT JOIN subscription_plans sp ON cs.plan_id = sp.id
                ORDER BY c.created_at DESC
            """)
        except:
            # Fallback: get companies without subscription info
            companies = query("""
                SELECT c.id, c.name, c.email, c.is_active,
                       NULL as sub_status, 
                       NULL as custom_price, 
                       NULL as end_date,
                       NULL as is_global_free,
                       NULL as free_access_until,
                       'free' as plan_name, 
                       0 as plan_price
                FROM companies c
                ORDER BY c.created_at DESC
            """)
        
        # Get subscription statistics - handle missing columns gracefully
        stats = {}
        try:
            result = query("SELECT COUNT(*) as count FROM company_subscriptions WHERE status = 'active'", one=True)
            stats['active_subs'] = result['count'] if result else 0
        except:
            stats['active_subs'] = 0
        
        try:
            result = query("SELECT COUNT(*) as count FROM company_subscriptions WHERE custom_price = 0", one=True)
            stats['free_subs'] = result['count'] if result else 0
        except:
            stats['free_subs'] = 0
        
        try:
            result = query("""
                SELECT COUNT(*) as count FROM company_subscriptions 
                WHERE end_date IS NOT NULL AND end_date <= DATE_ADD(NOW(), INTERVAL 7 DAY)
                AND status = 'active'
            """, one=True)
            stats['expiring_soon'] = result['count'] if result else 0
        except:
            stats['expiring_soon'] = 0
        
        return render_template('owner/subscriptions.html', 
                             plans=plans, 
                             companies=companies,
                             is_global_free=is_global_free,
                             stats=stats,
                             now=datetime.utcnow(),
                             timedelta=timedelta)
    except Exception as e:
        logger.exception(e)
        flash('Error loading subscriptions.', 'danger')
        return redirect(url_for('owner.dashboard'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/subscriptions/plan/<int:plan_id>', methods=['POST'])
@require_owner
def update_plan_price(plan_id):
    """Update a subscription plan's price."""
    new_monthly = request.form.get('price_monthly', type=float)
    new_yearly = request.form.get('price_yearly', type=float)
    
    if new_monthly and new_yearly:
        try:
            mutate("""
                UPDATE subscription_plans 
                SET price_monthly = %s, price_yearly = %s, updated_at = %s
                WHERE id = %s
            """, (new_monthly, new_yearly, datetime.utcnow(), plan_id))
            
            flash(f'Plan prices updated successfully.', 'success')
        except Exception as e:
            logger.exception(e)
            flash('Error updating plan prices.', 'danger')
    
    return redirect(url_for('owner.manage_subscriptions'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/subscriptions/company/<int:company_id>/custom-price', methods=['POST'])
@require_owner
def set_company_custom_price(company_id):
    """Set custom price for a specific company."""
    custom_price = request.form.get('custom_price', type=float)
    
    try:
        if custom_price is not None:
            mutate("""
                UPDATE company_subscriptions 
                SET custom_price = %s, updated_at = %s
                WHERE company_id = %s AND status IN ('active', 'trial')
            """, (custom_price, datetime.utcnow(), company_id))
            
            # Send email notification
            if custom_price == 0:
                send_subscription_change_email(
                    company_id, 'free_access',
                    f'Your subscription has been set to free ($0/month).'
                )
            else:
                send_subscription_change_email(
                    company_id, 'price_increase',
                    f'Your custom subscription price is now ${custom_price:.2f}/month.'
                )
            
            flash(f'Custom price set for company.', 'success')
        else:
            flash('Invalid price value.', 'warning')
    except Exception as e:
        logger.exception(e)
        flash('Error setting custom price.', 'danger')
    
    return redirect(url_for('owner.manage_subscriptions'))


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM EMAIL ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@owner_bp.route(f'/{OWNER_ROUTE_HASH}/email', methods=['GET', 'POST'])
@require_owner
def custom_email():
    """Send custom formal email to company admins."""
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'send_single':
                company_id = request.form.get('company_id', type=int)
                subject = request.form.get('subject', '').strip()
                message = request.form.get('message', '').strip()
                
                if company_id and subject and message:
                    success = send_custom_email_to_company(company_id, subject, message)
                    if success:
                        flash(f'Email sent successfully to company.', 'success')
                    else:
                        flash('Failed to send email. Check company admin email.', 'danger')
                else:
                    flash('Please fill all fields.', 'warning')
            
            elif action == 'send_bulk':
                company_ids = request.form.getlist('company_ids')
                subject = request.form.get('bulk_subject', '').strip()
                message = request.form.get('bulk_message', '').strip()
                
                if company_ids and subject and message:
                    sent_count = 0
                    for cid in company_ids:
                        if send_custom_email_to_company(int(cid), subject, message):
                            sent_count += 1
                    
                    flash(f'Email sent to {sent_count} companies.', 'success')
                else:
                    flash('Please select companies and fill all fields.', 'warning')
        
        # Get all companies for selection
        companies = query("""
            SELECT c.id, c.name, c.email, c.is_active
            FROM companies c
            ORDER BY c.name
        """)
        
        return render_template('owner/email.html', companies=companies)
    except Exception as e:
        logger.exception(e)
        flash('Error loading email page.', 'danger')
        return redirect(url_for('owner.dashboard'))


@owner_bp.route(f'/{OWNER_ROUTE_HASH}/email/company/<int:company_id>', methods=['GET', 'POST'])
@require_owner
def email_company(company_id):
    """Send email to a specific company."""
    try:
        company = query("SELECT * FROM companies WHERE id = %s", (company_id,), one=True)
        
        if not company:
            flash('Company not found.', 'warning')
            return redirect(url_for('owner.custom_email'))
        
        if request.method == 'POST':
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            
            if subject and message:
                success = send_custom_email_to_company(company_id, subject, message)
                if success:
                    flash(f'Email sent to {company["name"]}.', 'success')
                else:
                    flash('Failed to send email.', 'danger')
            else:
                flash('Please fill all fields.', 'warning')
        
        return render_template('owner/email_company.html', company=company)
    except Exception as e:
        logger.exception(e)
        flash('Error loading page.', 'danger')
        return redirect(url_for('owner.custom_email'))