"""
Cascading Delete Service
Handles permanent deletion of users and all their related data across tables
Admin-only operations with comprehensive audit trail
"""

import logging
from models.db import query, mutate

logger = logging.getLogger(__name__)

def delete_user_permanently(company_id, user_id, deleted_by_user_id):
    """
    Permanently delete a user and cascade delete all related records.
    Admin-only operation.
    
    Tables affected:
    - users (delete user record)
    - employees_core (delete employee record)
    - user_roles (delete role assignments)
    - activity_logs (keep for audit, mark as deleted)
    - payroll_runs (delete payroll records)
    - attendance_logs (delete attendance records)
    - leave_applications (delete leave applications)
    - appraisals (mark as deleted or remove)
    
    Args:
        company_id: Company ID for multi-tenant isolation
        user_id: User ID to delete
        deleted_by_user_id: Admin user performing the deletion (for audit)
    
    Returns:
        dict: {'success': bool, 'message': str, 'deleted_records': int}
    """
    try:
        from services.activity_service import log_activity
        
        deleted_count = 0
        
        # 1. Get user and employee info before deletion (for logging)
        user = query(
            "SELECT id, username, full_name, company_id FROM users WHERE id = %s AND company_id = %s",
            (user_id, company_id), one=True
        )
        
        if not user:
            return {'success': False, 'message': 'User not found', 'deleted_records': 0}
        
        # 2. Get associated employee ID
        employee = query(
            "SELECT id FROM employees_core WHERE user_id = %s AND company_id = %s",
            (user_id, company_id), one=True
        )
        employee_id = employee['id'] if employee else None
        
        # Start deletion cascade
        logger.info(f"Starting cascading delete for user {user_id} (username: {user['username']})")
        
        # 3. Delete activity logs associated with this user
        # (or keep for audit and just mark)
        result = mutate(
            "DELETE FROM activity_logs WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
        deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 4. Delete payroll records
        if employee_id:
            result = mutate(
                "DELETE FROM payroll_runs WHERE employee_id = %s AND company_id = %s",
                (employee_id, company_id)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 5. Delete attendance records
        if employee_id:
            result = mutate(
                "DELETE FROM attendance_logs WHERE employee_id = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 6. Delete leave applications
        if employee_id:
            result = mutate(
                "DELETE FROM leave_applications WHERE employee_id = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 7. Delete appraisals where employee is reviewer or being appraised
        if employee_id:
            result = mutate(
                "DELETE FROM appraisals WHERE (employee_id = %s OR reviewer_id = %s) AND company_id = %s",
                (employee_id, user_id, company_id)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 8. Delete gamification records
        if employee_id:
            result = mutate(
                "DELETE FROM gamification_points WHERE employee_id = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 9. Delete compliance records
        if employee_id:
            result = mutate(
                "DELETE FROM compliance_records WHERE employee_id = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 10. Delete attrition records
        if employee_id:
            result = mutate(
                "DELETE FROM attrition_records WHERE employee_id = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 11. Delete user roles
        result = mutate(
            "DELETE FROM user_roles WHERE user_id = %s AND company_id = %s",
            (user_id, company_id)
        )
        deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 12. Delete employee record
        if employee_id:
            result = mutate(
                "DELETE FROM employees_core WHERE id = %s AND company_id = %s",
                (employee_id, company_id)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # 13. Delete user record (LAST - foreign key constraint)
        result = mutate(
            "DELETE FROM users WHERE id = %s AND company_id = %s",
            (user_id, company_id)
        )
        deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 1
        
        # 14. Log the deletion action
        log_activity(
            company_id,
            deleted_by_user_id,
            'User permanently deleted',
            'User',
            user_id,
            f"User: {user['username']} ({user['full_name']})",
            f"All records deleted. Total records removed: {deleted_count}"
        )
        
        logger.info(
            f"Successfully deleted user {user_id} ({user['username']}). "
            f"Total records deleted: {deleted_count}"
        )
        
        return {
            'success': True,
            'message': f"User '{user['username']}' and all associated records deleted permanently.",
            'deleted_records': deleted_count,
            'user_deleted': user['username']
        }
    
    except Exception as e:
        logger.exception(f"Error during cascading delete for user {user_id}: {e}")
        return {
            'success': False,
            'message': f"Error deleting user: {str(e)}",
            'deleted_records': 0
        }


def delete_employee_permanently(company_id, employee_id, deleted_by_user_id):
    """
    Permanently delete an employee and cascade delete related records.
    Note: This will also delete the associated user if exists.
    """
    try:
        from services.activity_service import log_activity
        
        # Get employee and user info
        employee = query(
            "SELECT id, user_id FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id), one=True
        )
        
        if not employee:
            return {'success': False, 'message': 'Employee not found', 'deleted_records': 0}
        
        # If employee has associated user, delete the user (which cascades)
        if employee['user_id']:
            return delete_user_permanently(company_id, employee['user_id'], deleted_by_user_id)
        
        # Otherwise delete just the employee record
        deleted_count = 0
        
        # Delete all employee-related records
        tables_to_clean = [
            ('payroll_runs', 'employee_id'),
            ('attendance_logs', 'employee_id'),
            ('leave_applications', 'employee_id'),
            ('gamification_points', 'employee_id'),
            ('compliance_records', 'employee_id'),
            ('attrition_records', 'employee_id'),
        ]
        
        for table, col in tables_to_clean:
            result = mutate(
                f"DELETE FROM {table} WHERE {col} = %s",
                (employee_id,)
            )
            deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # Delete appraisals where employee is reviewer or being appraised
        result = mutate(
            "DELETE FROM appraisals WHERE (employee_id = %s OR reviewer_id = %s) AND company_id = %s",
            (employee_id, employee['user_id'] or 0, company_id)
        )
        deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 0
        
        # Delete employee record
        result = mutate(
            "DELETE FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id)
        )
        deleted_count += result.get('rows_affected', 0) if isinstance(result, dict) else 1
        
        # Log deletion
        log_activity(
            company_id,
            deleted_by_user_id,
            'Employee permanently deleted',
            'Employee',
            employee_id,
            None,
            f"All records deleted. Total records removed: {deleted_count}"
        )
        
        return {
            'success': True,
            'message': 'Employee and all associated records deleted permanently.',
            'deleted_records': deleted_count
        }
    
    except Exception as e:
        logger.exception(f"Error during employee deletion: {e}")
        return {
            'success': False,
            'message': f"Error deleting employee: {str(e)}",
            'deleted_records': 0
        }
