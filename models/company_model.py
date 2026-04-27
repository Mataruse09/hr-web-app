from models.db import query, mutate
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


def create_company(name, industry, address, phone, email, website, terms_accepted=False):
    return mutate(
        "INSERT INTO companies (name, industry, address, phone, email, website, terms_accepted, terms_accepted_at, terms_version) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (name, industry, address, phone, email, website, terms_accepted, datetime.utcnow() if terms_accepted else None, '1.0')
    )


def get_by_id(company_id: int):
    try:
        return query(
            "SELECT id, name, industry, address, phone, email, website, is_active "
            "FROM companies WHERE id = %s AND is_active = TRUE",
            (company_id,), one=True
        )
    except Exception as e:
        logger.error(f"Error getting company by id {company_id}: {e}")
        return None


def get_by_id_any_status(company_id: int):
    """Get company by ID regardless of active status - for security checks"""
    try:
        return query(
            "SELECT id, name, industry, address, phone, email, website, is_active, ban_reason, ban_type, banned_at, banned_by "
            "FROM companies WHERE id = %s",
            (company_id,), one=True
        )
    except Exception as e:
        logger.error(f"Error getting company by id any status {company_id}: {e}")
        logger.error(traceback.format_exc())
        return None


def get_by_name(name: str):
    try:
        return query(
            "SELECT id, name, industry, address, phone, email, website, is_active "
            "FROM companies WHERE name = %s AND is_active = TRUE",
            (name,), one=True
        )
    except Exception as e:
        logger.error(f"Error getting company by name {name}: {e}")
        return None


def all_active_companies():
    try:
        return query(
            "SELECT id, name FROM companies WHERE is_active = TRUE ORDER BY name"
        )
    except Exception as e:
        logger.error(f"Error getting all active companies: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# BAN SYSTEM FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def ban_company(company_id: int, reason: str, ban_type: str = 'manual', banned_by: int = None, auto_trigger: str = None):
    """
    Ban a company (manual or auto ban).
    """
    return mutate(
        """UPDATE companies 
           SET is_banned = TRUE, ban_reason = %s, banned_at = %s, banned_by = %s, 
               ban_type = %s, auto_ban_trigger = %s, is_active = FALSE
           WHERE id = %s""",
        (reason, datetime.utcnow(), banned_by, ban_type, auto_trigger, company_id)
    )


def unban_company(company_id: int):
    """
    Unban a company - reactivate their account.
    """
    return mutate(
        """UPDATE companies 
           SET is_banned = FALSE, ban_reason = NULL, banned_at = NULL, banned_by = NULL, 
               ban_type = 'manual', auto_ban_trigger = NULL, is_active = TRUE
           WHERE id = %s""",
        (company_id,)
    )


def get_banned_companies():
    """
    Get all banned companies.
    """
    return query(
        """SELECT c.*, u.username as banned_by_user 
           FROM companies c
           LEFT JOIN users u ON c.banned_by = u.id
           WHERE c.is_banned = TRUE
           ORDER BY c.banned_at DESC"""
    )


def is_company_banned(company_id: int) -> bool:
    """
    Check if a company is banned.
    """
    result = query(
        "SELECT is_banned FROM companies WHERE id = %s",
        (company_id,), one=True
    )
    return result.get('is_banned', False) if result else False


def get_company_ban_info(company_id: int):
    """
    Get detailed ban information for a company.
    """
    return query(
        """SELECT c.*, u.username as banned_by_user 
           FROM companies c
           LEFT JOIN users u ON c.banned_by = u.id
           WHERE c.id = %s""",
        (company_id,), one=True
    )


# ═══════════════════════════════════════════════════════════════════════════
# ABUSE REPORTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_abuse_report(company_id: int, reporter_id: int, report_type: str, description: str, evidence: dict = None):
    """
    Create a new abuse report.
    """
    import json
    return mutate(
        """INSERT INTO abuse_reports (company_id, reporter_id, report_type, description, evidence) 
           VALUES (%s,%s,%s,%s,%s)""",
        (company_id, reporter_id, report_type, description, json.dumps(evidence) if evidence else None)
    )


def get_company_abuse_reports(company_id: int):
    """
    Get all abuse reports for a company.
    """
    return query(
        """SELECT ar.*, u.username as reporter_username
           FROM abuse_reports ar
           LEFT JOIN users u ON ar.reporter_id = u.id
           WHERE ar.company_id = %s
           ORDER BY ar.created_at DESC""",
        (company_id,)
    )


def get_all_abuse_reports(status: str = None):
    """
    Get all abuse reports, optionally filtered by status.
    """
    if status:
        return query(
            """SELECT ar.*, c.name as company_name, u.username as reporter_username
               FROM abuse_reports ar
               JOIN companies c ON ar.company_id = c.id
               LEFT JOIN users u ON ar.reporter_id = u.id
               WHERE ar.status = %s
               ORDER BY ar.created_at DESC""",
            (status,)
        )
    return query(
        """SELECT ar.*, c.name as company_name, u.username as reporter_username
           FROM abuse_reports ar
           JOIN companies c ON ar.company_id = c.id
           LEFT JOIN users u ON ar.reporter_id = u.id
           ORDER BY ar.created_at DESC"""
    )


def update_abuse_report_status(report_id: int, status: str, resolved_by: int = None, resolution_notes: str = None):
    """
    Update abuse report status.
    """
    return mutate(
        """UPDATE abuse_reports 
           SET status = %s, resolved_by = %s, resolution_notes = %s, resolved_at = %s, updated_at = %s
           WHERE id = %s""",
        (status, resolved_by, resolution_notes, datetime.utcnow(), datetime.utcnow(), report_id)
    )


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN NOTIFICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_admin_notification(user_id: int, title: str, message: str, notification_type: str = 'info', link: str = None):
    """
    Create a notification for admin users.
    """
    return mutate(
        """INSERT INTO admin_notifications (user_id, title, message, notification_type, link) 
           VALUES (%s,%s,%s,%s,%s)""",
        (user_id, title, message, notification_type, link)
    )


def notify_admins_of_abuse(title: str, message: str, company_id: int = None, link: str = None):
    """
    Send abuse notification to all admin users.
    """
    # Get all admin users
    admins = query("SELECT id FROM users WHERE role = 'Admin'")
    
    for admin in admins:
        create_admin_notification(
            admin['id'], 
            title, 
            message, 
            'abuse',
            link or f'/admin/companies/{company_id}'
        )


def get_unread_admin_notifications(user_id: int):
    """
    Get unread notifications for an admin.
    """
    return query(
        """SELECT * FROM admin_notifications 
           WHERE user_id = %s AND is_read = FALSE 
           ORDER BY created_at DESC""",
        (user_id,)
    )


def mark_notification_read(notification_id: int):
    """
    Mark a notification as read.
    """
    return mutate(
        "UPDATE admin_notifications SET is_read = TRUE WHERE id = %s",
        (notification_id,)
    )


def mark_all_notifications_read(user_id: int):
    """
    Mark all notifications as read for a user.
    """
    return mutate(
        "UPDATE admin_notifications SET is_read = TRUE WHERE user_id = %s",
        (user_id,)
    )


# ═══════════════════════════════════════════════════════════════════════════
# AUTO BAN TRIGGER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def check_and_auto_ban_company(company_id: int) -> bool:
    """
    Check if company should be auto-banned based on abuse triggers.
    Returns True if company was banned.
    """
    # Check for multiple abuse reports with high severity
    high_severe_reports = query(
        """SELECT COUNT(*) as count FROM abuse_reports 
           WHERE company_id = %s AND severity IN ('high', 'critical') AND status != 'resolved'""",
        (company_id,), one=True
    )
    
    if high_severe_reports and high_severe_reports.get('count', 0) >= 3:
        # Auto ban for repeated high severity reports
        ban_company(
            company_id, 
            "Auto-banned due to repeated abuse reports (3+ high/critical severity)", 
            'auto',
            auto_trigger='repeated_abuse'
        )
        notify_admins_of_abuse(
            "Company Auto-Banned",
            f"A company (ID: {company_id}) has been automatically banned due to repeated abuse reports.",
            company_id
        )
        return True
    
    return False