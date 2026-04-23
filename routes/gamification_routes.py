"""
Gamification Routes - Points, badges, leaderboards
Employee engagement and motivation system
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime

from utils import login_required, roles_required
from models.db import query, mutate
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

gamification_bp = Blueprint('gamification', __name__)


@gamification_bp.route('/gamification/leaderboard')
@login_required
def leaderboard():
    """View employee leaderboard (points, levels, badges)."""
    company_id = session['company_id']
    
    try:
        leaderboard_data = query(
            """SELECT gp.employee_id, ec.first_name, ec.last_name, ec.job_title,
                      gp.points, gp.level, gp.badges
               FROM gamification_points gp
               LEFT JOIN employees_core ec ON gp.employee_id = ec.id
               WHERE gp.company_id = %s AND ec.company_id = %s
               ORDER BY gp.points DESC, gp.level DESC
               LIMIT 100""",
            (company_id, company_id)
        )
        
        return render_template('gamification/leaderboard.html', leaderboard=leaderboard_data or [])
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading leaderboard.', 'danger')
        return redirect(url_for('dashboard.index'))


@gamification_bp.route('/gamification/my-profile')
@login_required
def my_profile():
    """View personal gamification profile."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        # Get employee ID for current user
        employee = query(
            "SELECT id FROM employees_core WHERE user_id = %s AND company_id = %s",
            (user_id, company_id), one=True
        )
        
        if not employee:
            flash('Employee record not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Get gamification data
        gamification = query(
            "SELECT * FROM gamification_points WHERE company_id = %s AND employee_id = %s",
            (company_id, employee['id']), one=True
        )
        
        if not gamification:
            # Initialize if doesn't exist
            mutate(
                """INSERT INTO gamification_points 
                   (company_id, employee_id, points, level, badges, achievements) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (company_id, employee['id'], 0, 1, '[]', '[]')
            )
            gamification = {'points': 0, 'level': 1, 'badges': '[]', 'achievements': '[]'}
        
        return render_template('gamification/profile.html', profile=gamification)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading profile.', 'danger')
        return redirect(url_for('dashboard.index'))


@gamification_bp.route('/gamification/award-points', methods=['POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def award_points():
    """Award points to employee (HR/Manager/Admin only)."""
    company_id = session['company_id']
    admin_user_id = session['user_id']
    
    try:
        employee_id = request.form.get('employee_id', type=int)
        points = request.form.get('points', type=int, default=10)
        reason = request.form.get('reason', '').strip()
        
        if not employee_id or points <= 0:
            return jsonify({'error': 'Invalid employee or points'}), 400
        
        # Verify employee exists
        employee = query(
            "SELECT id FROM employees_core WHERE id = %s AND company_id = %s",
            (employee_id, company_id), one=True
        )
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get or create gamification record
        gamification = query(
            "SELECT * FROM gamification_points WHERE company_id = %s AND employee_id = %s",
            (company_id, employee_id), one=True
        )
        
        if gamification:
            new_points = gamification['points'] + points
            mutate(
                "UPDATE gamification_points SET points = %s WHERE company_id = %s AND employee_id = %s",
                (new_points, company_id, employee_id)
            )
        else:
            mutate(
                """INSERT INTO gamification_points 
                   (company_id, employee_id, points, level, badges, achievements) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (company_id, employee_id, points, 1, '[]', '[]')
            )
        
        # Log activity
        log_activity(
            company_id, admin_user_id, 'Points awarded',
            'Employee', employee_id, None,
            f"{points} points awarded. Reason: {reason}"
        )
        
        return jsonify({'success': True, 'message': f'{points} points awarded'})
    
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@gamification_bp.route('/gamification/achievements')
@login_required
def view_achievements():
    """View possible achievements and unlocked badges."""
    achievements = [
        {'title': '⭐ First Day', 'description': 'Completed first login'},
        {'title': '📋 Perfect Attendance', 'description': '30 days without absence'},
        {'title': '🎯 Performance Star', 'description': 'Appraisal rating 5/5'},
        {'title': '💯 Team Player', 'description': 'Helped 5 teammates'},
        {'title': '🚀 Go-Getter', 'description': 'Completed 10 tasks ahead of schedule'},
    ]
    
    return render_template('gamification/achievements.html', achievements=achievements)
