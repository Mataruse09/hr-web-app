"""
Attrition Tracking Routes - Exit management and analytics
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime

from utils import login_required, roles_required
from models.db import query, mutate
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

attrition_bp = Blueprint('attrition', __name__)


@attrition_bp.route('/attrition')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def list_attrition():
    """List all employee exits and attrition records."""
    company_id = session['company_id']
    
    try:
        attrition_records = query(
            """SELECT ar.*, ec.first_name, ec.last_name, ec.job_title,
                      ec.hire_date
               FROM attrition_records ar
               LEFT JOIN employees_core ec ON ar.employee_id = ec.id
               WHERE ec.company_id = %s
               ORDER BY ar.exit_date DESC
               LIMIT 100""",
            (company_id,)
        )
        
        # Calculate attrition rate
        total_employees = query(
            "SELECT COUNT(*) as count FROM employees_core WHERE company_id = %s AND status = 'Active'",
            (company_id,), one=True
        )
        
        attrition_this_year = query(
            """SELECT COUNT(*) as count FROM attrition_records ar
               LEFT JOIN employees_core ec ON ar.employee_id = ec.id
               WHERE ec.company_id = %s AND YEAR(ar.exit_date) = YEAR(CURDATE())""",
            (company_id,), one=True
        )
        
        attrition_rate = 0
        if total_employees and total_employees['count'] > 0:
            total = total_employees['count'] + (attrition_this_year['count'] or 0)
            attrition_rate = ((attrition_this_year['count'] or 0) / total * 100)
        
        return render_template(
            'attrition/list.html',
            attrition_records=attrition_records or [],
            attrition_rate=f"{attrition_rate:.1f}%"
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading attrition records.', 'danger')
        return redirect(url_for('dashboard.index'))


@attrition_bp.route('/attrition/record/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def record_exit(employee_id):
    """Record employee exit/resignation."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        # Get employee
        employee = query(
            "SELECT id, first_name, last_name, job_title FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id), one=True
        )
        
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        if request.method == 'POST':
            exit_date = request.form.get('exit_date', '').strip()
            exit_reason = request.form.get('exit_reason', '').strip()
            exit_interview = request.form.get('exit_interview', '').strip()
            final_settlement = request.form.get('final_settlement', type=float, default=0)
            
            if not exit_date:
                flash('Exit date is required.', 'danger')
                return render_template('attrition/record.html', employee=employee)
            
            try:
                # Check if already recorded
                existing = query(
                    "SELECT id FROM attrition_records WHERE employee_id = %s",
                    (employee_id,), one=True
                )
                
                if existing:
                    flash('Exit already recorded for this employee.', 'warning')
                    return render_template('attrition/record.html', employee=employee)
                
                # Record exit
                mutate(
                    """INSERT INTO attrition_records 
                       (employee_id, exit_date, reason, exit_interview_notes, 
                        final_settlement_amount, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (employee_id, exit_date, exit_reason, exit_interview,
                     final_settlement, datetime.utcnow())
                )
                
                # Update employee status
                mutate(
                    "UPDATE employees_core SET status = %s WHERE id = %s",
                    ('Inactive', employee_id)
                )
                
                # Log activity
                log_activity(
                    company_id, user_id, 'Employee exit recorded',
                    'Employee', employee_id,
                    'Active', f"Reason: {exit_reason}"
                )
                
                flash(f'Exit recorded for {employee["first_name"]} {employee["last_name"]}.', 'success')
                return redirect(url_for('attrition.list_attrition'))
            
            except Exception as e:
                logger.exception(e)
                flash('Error recording exit.', 'danger')
        
        return render_template('attrition/record.html', employee=employee)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading form.', 'danger')
        return redirect(url_for('dashboard.index'))


@attrition_bp.route('/attrition/analytics')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def attrition_analytics():
    """View attrition analytics and trends."""
    company_id = session['company_id']
    
    try:
        # Top reasons for exit
        exit_reasons = query(
            """SELECT reason, COUNT(*) as count FROM attrition_records ar
               LEFT JOIN employees_core ec ON ar.employee_id = ec.id
               WHERE ec.company_id = %s
               GROUP BY reason
               ORDER BY count DESC
               LIMIT 10""",
            (company_id,)
        )
        
        # Attrition by month
        monthly_attrition = query(
            """SELECT DATE_TRUNC('month', ar.exit_date) as month, COUNT(*) as count
               FROM attrition_records ar
               LEFT JOIN employees_core ec ON ar.employee_id = ec.id
               WHERE ec.company_id = %s
               GROUP BY DATE_TRUNC('month', ar.exit_date)
               ORDER BY month DESC
               LIMIT 12""",
            (company_id,)
        )
        
        return render_template(
            'attrition/analytics.html',
            exit_reasons=exit_reasons or [],
            monthly_attrition=monthly_attrition or []
        )
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading analytics.', 'danger')
        return redirect(url_for('dashboard.index'))
