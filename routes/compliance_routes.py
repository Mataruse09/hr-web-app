"""
Compliance Tracking Routes - Policy compliance and tracking
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime

from utils import login_required, roles_required
from models.db import query, mutate
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__)


# Predefined compliance policies
COMPLIANCE_POLICIES = [
    {'name': 'Data Privacy Training', 'type': 'Training', 'frequency': 'Annual'},
    {'name': 'Code of Conduct', 'type': 'Policy', 'frequency': 'Once'},
    {'name': 'Health & Safety', 'type': 'Training', 'frequency': 'Annual'},
    {'name': 'Anti-Harassment Policy', 'type': 'Policy', 'frequency': 'Annual'},
    {'name': 'ISO Certification', 'type': 'Certification', 'frequency': 'Biennial'},
]


@compliance_bp.route('/compliance')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Employee')
def list_compliance():
    """List all compliance records."""
    company_id = session['company_id']
    user_role = session.get('role', 'Employee')
    user_id = session.get('user_id')
    
    try:
        # Employees can only see their own compliance records
        if user_role == 'Employee':
            from models.employee_model import get_by_user_id
            employee = get_by_user_id(user_id, company_id)
            if employee:
                compliance_records = query(
                    """SELECT cr.*, ec.first_name, ec.last_name, ec.job_title
                       FROM compliance_records cr
                       LEFT JOIN employees_core ec ON cr.employee_id = ec.id
                       WHERE cr.employee_id = %s AND ec.company_id = %s
                       ORDER BY cr.due_date ASC
                       LIMIT 100""",
                    (employee['id'], company_id)
                )
            else:
                compliance_records = []
        elif user_role in ['Admin', 'HR', 'CHRO']:
            # Admin, HR, CHRO can see all
            compliance_records = query(
                """SELECT cr.*, ec.first_name, ec.last_name, ec.job_title
                   FROM compliance_records cr
                   LEFT JOIN employees_core ec ON cr.employee_id = ec.id
                   WHERE ec.company_id = %s
                   ORDER BY cr.due_date ASC
                   LIMIT 100""",
                (company_id,)
            )
        else:
            compliance_records = []
        
        return render_template('compliance/list.html', compliance_records=compliance_records or [])
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading compliance records.', 'danger')
        return redirect(url_for('dashboard.index'))


@compliance_bp.route('/compliance/assign/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def assign_compliance(employee_id):
    """Assign compliance policy to employee."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        # Get employee
        employee = query(
            "SELECT id, first_name, last_name FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id), one=True
        )
        
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('compliance.list_compliance'))
        
        if request.method == 'POST':
            policy_name = request.form.get('policy_name', '').strip()
            compliance_type = request.form.get('compliance_type', '').strip()
            status = request.form.get('status', 'Pending').strip()
            due_date = request.form.get('due_date', '').strip()
            
            if not all([policy_name, compliance_type, due_date]):
                flash('All fields are required.', 'danger')
                return render_template('compliance/assign.html', employee=employee, policies=COMPLIANCE_POLICIES)
            
            try:
                mutate(
                    """INSERT INTO compliance_records 
                       (company_id, employee_id, policy_name, compliance_type, status, due_date, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (company_id, employee_id, policy_name, compliance_type, status, due_date, datetime.utcnow())
                )
                
                log_activity(
                    company_id, user_id, 'Compliance assigned',
                    'Compliance', employee_id,
                    None, f"Policy: {policy_name}"
                )
                
                flash('Compliance assigned successfully!', 'success')
                return redirect(url_for('compliance.list_compliance'))
            
            except Exception as e:
                logger.exception(e)
                flash('Error assigning compliance.', 'danger')
        
        return render_template('compliance/assign.html', employee=employee, policies=COMPLIANCE_POLICIES)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading form.', 'danger')
        return redirect(url_for('compliance.list_compliance'))


@compliance_bp.route('/compliance/<int:compliance_id>/mark-complete', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def mark_complete(compliance_id):
    """Mark compliance as completed."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        # Get compliance record
        compliance = query(
            """SELECT cr.*, ec.company_id FROM compliance_records cr
               LEFT JOIN employees_core ec ON cr.employee_id = ec.id
               WHERE cr.id = %s""",
            (compliance_id,), one=True
        )
        
        if not compliance or compliance['company_id'] != company_id:
            return jsonify({'error': 'Record not found'}), 404
        
        # Check permission (employee can only mark their own, others need HR/Admin)
        if compliance['employee_id'] != query(
            "SELECT id FROM employees_core WHERE user_id = %s AND company_id = %s",
            (user_id, company_id), one=True
        )['id'] and session['role'] not in ['Admin', 'HR', 'CHRO']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        mutate(
            "UPDATE compliance_records SET status = %s, completed_at = %s WHERE id = %s",
            ('Completed', datetime.utcnow(), compliance_id)
        )
        
        log_activity(
            company_id, user_id, 'Compliance completed',
            'Compliance', compliance_id
        )
        
        return jsonify({'success': True, 'message': 'Compliance marked as completed'})
    
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@compliance_bp.route('/compliance/dashboard')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def compliance_dashboard():
    """View compliance dashboard with overdue items."""
    company_id = session['company_id']
    
    try:
        # Overdue compliance items
        overdue = query(
            """SELECT cr.*, ec.first_name, ec.last_name, ec.job_title
               FROM compliance_records cr
               LEFT JOIN employees_core ec ON cr.employee_id = ec.id
               WHERE ec.company_id = %s AND cr.status = 'Pending' 
                 AND cr.due_date < CURDATE()
               ORDER BY cr.due_date ASC
               LIMIT 20""",
            (company_id,)
        )
        
        # Upcoming (due in next 7 days)
        upcoming = query(
            """SELECT cr.*, ec.first_name, ec.last_name, ec.job_title
               FROM compliance_records cr
               LEFT JOIN employees_core ec ON cr.employee_id = ec.id
               WHERE ec.company_id = %s AND cr.status = 'Pending' 
                 AND cr.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
               ORDER BY cr.due_date ASC
               LIMIT 20""",
            (company_id,)
        )
        
        # Completion stats
        stats = query(
            """SELECT 
                 COUNT(*) as total,
                 SUM(CASE WHEN cr.status = 'Completed' THEN 1 ELSE 0 END) as completed,
                 SUM(CASE WHEN cr.status = 'Pending' THEN 1 ELSE 0 END) as pending
               FROM compliance_records cr
               LEFT JOIN employees_core ec ON cr.employee_id = ec.id
               WHERE ec.company_id = %s""",
            (company_id,), one=True
        )
        
        completion_rate = 0
        if stats and stats['total'] > 0:
            completion_rate = (stats['completed'] / stats['total'] * 100)
        
        return render_template(
            'compliance/dashboard.html',
            overdue=overdue or [],
            upcoming=upcoming or [],
            stats=stats or {},
            completion_rate=f"{completion_rate:.1f}%"
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('dashboard.index'))
