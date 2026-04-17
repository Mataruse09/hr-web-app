"""
Activity/Audit Logging Service - Track user actions for compliance
"""
from models.db import mutate, query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ACTION_TYPES = {
    'LOGIN': 'User logged in',
    'LOGOUT': 'User logged out',
    'CREATE_EMPLOYEE': 'Employee created',
    'UPDATE_EMPLOYEE': 'Employee updated',
    'DELETE_EMPLOYEE': 'Employee deleted',
    'MARK_ATTENDANCE': 'Attendance marked',
    'PROCESS_PAYROLL': 'Payroll processed',
    'APPROVE_LEAVE': 'Leave approved',
    'CREATE_APPRAISAL': 'Appraisal created',
    'UPDATE_SYSTEM_SETTING': 'System setting changed',
    'EXPORT_DATA': 'Data exported',
    'USER_ROLE_CHANGED': 'User role modified',
}


def log_activity(company_id: int, user_id: int, action: str, entity_type: str = None, 
                 entity_id: int = None, old_value: str = None, new_value: str = None, 
                 ip_address: str = None):
    """Log user activity for audit trail."""
    try:
        mutate("""
            INSERT INTO activity_logs 
            (company_id, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (company_id, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, datetime.utcnow()))
        logger.info(f"Activity logged: {action} by user {user_id} in company {company_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        return False


def get_activity_logs(company_id: int, limit: int = 100, offset: int = 0):
    """Retrieve activity logs for a company."""
    return query("""
        SELECT 
            al.id, al.user_id, al.action, al.entity_type, al.entity_id,
            al.old_value, al.new_value, al.created_at,
            u.full_name, u.username
        FROM activity_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE al.company_id = %s
        ORDER BY al.created_at DESC
        LIMIT %s OFFSET %s
    """, (company_id, limit, offset))


def get_user_activity_logs(company_id: int, user_id: int, limit: int = 50):
    """Get activity logs for a specific user."""
    return query("""
        SELECT * FROM activity_logs
        WHERE company_id = %s AND user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (company_id, user_id, limit))


def get_employee_activity_logs(company_id: int, employee_id: int):
    """Get all activities related to an employee."""
    return query("""
        SELECT 
            al.id, al.action, al.entity_type, al.created_at,
            u.full_name as performed_by
        FROM activity_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE al.company_id = %s AND al.entity_id = %s
        ORDER BY al.created_at DESC
    """, (company_id, employee_id))


def get_activity_summary(company_id: int, days: int = 7):
    """Get activity summary for the past N days."""
    return query("""
        SELECT 
            DATE(created_at) as date,
            action,
            COUNT(*) as count
        FROM activity_logs
        WHERE company_id = %s AND created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(created_at), action
        ORDER BY DATE(created_at) DESC
    """, (company_id, days))
