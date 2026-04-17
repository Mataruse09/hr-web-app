"""
Appraisal Routes - Performance reviews and ratings system
HR/Manager/Admin can create and manage employee appraisals
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime

from utils import login_required, roles_required
from models.db import query, mutate
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

appraisal_bp = Blueprint('appraisals', __name__)


@appraisal_bp.route('/appraisals')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def list_appraisals():
    """List all appraisals (filtered by role)."""
    company_id = session['company_id']
    user_role = session['role']
    
    try:
        if user_role == 'Admin':
            # Admins see all appraisals
            appraisals = query(
                """SELECT a.id, a.employee_id, ec.first_name, ec.last_name, ec.job_title,
                          a.reviewer_id, u.full_name as reviewer_name, a.overall_rating,
                          a.status, a.created_at
                   FROM appraisals a
                   LEFT JOIN employees_core ec ON a.employee_id = ec.id
                   LEFT JOIN users u ON a.reviewer_id = u.id
                   WHERE a.company_id = %s
                   ORDER BY a.created_at DESC
                   LIMIT 100""",
                (company_id,)
            )
        else:
            # Others see only appraisals they reviewed or were reviewed
            appraisals = query(
                """SELECT a.id, a.employee_id, ec.first_name, ec.last_name, ec.job_title,
                          a.reviewer_id, u.full_name as reviewer_name, a.overall_rating,
                          a.status, a.created_at
                   FROM appraisals a
                   LEFT JOIN employees_core ec ON a.employee_id = ec.id
                   LEFT JOIN users u ON a.reviewer_id = u.id
                   WHERE a.company_id = %s AND (a.reviewer_id = %s OR a.employee_id IN 
                         (SELECT id FROM employees_core WHERE user_id = %s))
                   ORDER BY a.created_at DESC
                   LIMIT 100""",
                (company_id, session['user_id'], session['user_id'])
            )
        
        return render_template('appraisals/list.html', appraisals=appraisals or [])
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading appraisals.', 'danger')
        return redirect(url_for('dashboard.index'))


@appraisal_bp.route('/appraisals/create/<int:employee_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def create_appraisal(employee_id):
    """Create new appraisal for an employee."""
    company_id = session['company_id']
    reviewer_id = session['user_id']
    
    try:
        # Verify employee exists and belongs to company
        employee = query(
            "SELECT id, first_name, last_name, job_title FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id), one=True
        )
        
        if not employee:
            flash('Employee not found.', 'danger')
            return redirect(url_for('appraisals.list_appraisals'))
        
        if request.method == 'POST':
            try:
                # Get ratings
                communication = int(request.form.get('communication', 3))
                teamwork = int(request.form.get('teamwork', 3))
                innovation = int(request.form.get('innovation', 3))
                punctuality = int(request.form.get('punctuality', 3))
                comments = request.form.get('comments', '').strip()
                
                # Validate ratings
                for rating in [communication, teamwork, innovation, punctuality]:
                    if rating < 1 or rating > 5:
                        flash('All ratings must be between 1 and 5.', 'danger')
                        return render_template('appraisals/create.html', employee=employee)
                
                # Calculate overall rating
                overall_rating = (communication + teamwork + innovation + punctuality) / 4
                
                # Create appraisal
                mutate(
                    """INSERT INTO appraisals 
                       (company_id, employee_id, reviewer_id, communication_rating, 
                        teamwork_rating, innovation_rating, punctuality_rating, 
                        overall_rating, comments, status, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (company_id, employee_id, reviewer_id, communication, teamwork,
                     innovation, punctuality, overall_rating, comments, 'Draft',
                     datetime.utcnow())
                )
                
                # Log activity
                log_activity(
                    company_id, reviewer_id, 'Appraisal created',
                    'Appraisal', employee_id,
                    None, f"Rating: {overall_rating:.1f}/5"
                )
                
                flash(f'Appraisal for {employee["first_name"]} created successfully!', 'success')
                return redirect(url_for('appraisals.list_appraisals'))
            
            except Exception as e:
                logger.exception(e)
                flash('Error creating appraisal.', 'danger')
        
        return render_template('appraisals/create.html', employee=employee)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading appraisal form.', 'danger')
        return redirect(url_for('appraisals.list_appraisals'))


@appraisal_bp.route('/appraisals/<int:appraisal_id>')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def view_appraisal(appraisal_id):
    """View specific appraisal details."""
    company_id = session['company_id']
    
    try:
        appraisal = query(
            """SELECT a.*, ec.first_name, ec.last_name, ec.job_title,
                     u.full_name as reviewer_name
              FROM appraisals a
              LEFT JOIN employees_core ec ON a.employee_id = ec.id
              LEFT JOIN users u ON a.reviewer_id = u.id
              WHERE a.id = %s AND a.company_id = %s""",
            (appraisal_id, company_id), one=True
        )
        
        if not appraisal:
            flash('Appraisal not found.', 'danger')
            return redirect(url_for('appraisals.list_appraisals'))
        
        return render_template('appraisals/view.html', appraisal=appraisal)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading appraisal.', 'danger')
        return redirect(url_for('appraisals.list_appraisals'))


@appraisal_bp.route('/appraisals/<int:appraisal_id>/submit', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def submit_appraisal(appraisal_id):
    """Submit appraisal for approval."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        appraisal = query(
            "SELECT id, reviewer_id FROM appraisals WHERE id = %s AND company_id = %s",
            (appraisal_id, company_id), one=True
        )
        
        if not appraisal:
            return jsonify({'error': 'Appraisal not found'}), 404
        
        if appraisal['reviewer_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        mutate(
            "UPDATE appraisals SET status = %s, updated_at = %s WHERE id = %s",
            ('Submitted', datetime.utcnow(), appraisal_id)
        )
        
        log_activity(company_id, user_id, 'Appraisal submitted', 'Appraisal', appraisal_id)
        
        return jsonify({'success': True, 'message': 'Appraisal submitted for approval'})
    
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@appraisal_bp.route('/appraisals/<int:appraisal_id>/approve', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def approve_appraisal(appraisal_id):
    """Approve appraisal (HR/CHRO/Admin only)."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        mutate(
            """UPDATE appraisals SET status = %s, approved_by = %s, 
               approved_at = %s WHERE id = %s AND company_id = %s""",
            ('Approved', user_id, datetime.utcnow(), appraisal_id, company_id)
        )
        
        log_activity(company_id, user_id, 'Appraisal approved', 'Appraisal', appraisal_id)
        
        flash('Appraisal approved successfully.', 'success')
        return redirect(url_for('appraisals.view_appraisal', appraisal_id=appraisal_id))
    
    except Exception as e:
        logger.exception(e)
        flash('Error approving appraisal.', 'danger')
        return redirect(url_for('appraisals.view_appraisal', appraisal_id=appraisal_id))
