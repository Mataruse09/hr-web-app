"""
Labour Forecasting Routes - Workforce planning and predictions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import logging
from datetime import datetime, timedelta

from utils import login_required, roles_required
from models.db import query, mutate
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

forecasting_bp = Blueprint('forecasting', __name__)


@forecasting_bp.route('/forecasting')
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def list_forecasts():
    """List all labour forecasts."""
    company_id = session['company_id']
    
    try:
        forecasts = query(
            """SELECT lf.*, d.name as department_name 
               FROM labour_forecasts lf
               LEFT JOIN departments d ON lf.department_id = d.id
               WHERE lf.company_id = %s
               ORDER BY lf.forecast_month DESC
               LIMIT 50""",
            (company_id,)
        )
        
        return render_template('forecasting/list.html', forecasts=forecasts or [])
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading forecasts.', 'danger')
        return redirect(url_for('dashboard.index'))


@forecasting_bp.route('/forecasting/create', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'HR', 'CHRO', 'Manager')
def create_forecast():
    """Create new labour forecast."""
    company_id = session['company_id']
    user_id = session['user_id']
    
    try:
        # Get departments
        departments = query(
            "SELECT id, name AS department_name FROM departments WHERE company_id = %s",
            (company_id,)
        ) or []
        
        if request.method == 'POST':
            department_id = request.form.get('department_id', type=int)
            forecast_month = request.form.get('forecast_month', '').strip()
            current_headcount = request.form.get('current_headcount', type=int)
            projected_headcount = request.form.get('projected_headcount', type=int)
            hiring_budget = request.form.get('hiring_budget', type=float)
            notes = request.form.get('notes', '').strip()
            
            if not all([department_id, forecast_month, current_headcount is not None, 
                       projected_headcount is not None]):
                flash('All required fields must be filled.', 'danger')
                return render_template('forecasting/create.html', departments=departments)
            
            try:
                mutate(
                    """INSERT INTO labour_forecasts 
                       (company_id, department_id, forecast_month, current_headcount, 
                        projected_headcount, hiring_budget, notes, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (company_id, department_id, forecast_month, current_headcount,
                     projected_headcount, hiring_budget, notes, datetime.utcnow())
                )
                
                log_activity(
                    company_id, user_id, 'Forecast created',
                    'Forecast', department_id,
                    None, f"Current: {current_headcount}, Projected: {projected_headcount}"
                )
                
                flash('Forecast created successfully!', 'success')
                return redirect(url_for('forecasting.list_forecasts'))
            
            except Exception as e:
                logger.exception(e)
                flash('Error creating forecast.', 'danger')
        
        return render_template('forecasting/create.html', departments=departments)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading form.', 'danger')
        return redirect(url_for('forecasting.list_forecasts'))


@forecasting_bp.route('/forecasting/<int:forecast_id>')
@login_required
@roles_required('Admin', 'HR', 'CHRO')
def view_forecast(forecast_id):
    """View forecast details and recommendations."""
    company_id = session['company_id']
    
    try:
        forecast = query(
            """SELECT lf.*, d.name as department_name FROM labour_forecasts lf
               LEFT JOIN departments d ON lf.department_id = d.id
               WHERE lf.id = %s AND lf.company_id = %s""",
            (forecast_id, company_id), one=True
        )
        
        if not forecast:
            flash('Forecast not found.', 'danger')
            return redirect(url_for('forecasting.list_forecasts'))
        
        # Calculate recommendations
        headcount_change = forecast['projected_headcount'] - forecast['current_headcount']
        recommendations = []
        
        if headcount_change > 0:
            recommendations.append(f"🔴 Need to hire {headcount_change} employees")
        elif headcount_change < 0:
            recommendations.append(f"🟢 May have {abs(headcount_change)} surplus employees")
        else:
            recommendations.append("🟡 Headcount expected to remain stable")
        
        forecast['recommendations'] = recommendations
        return render_template('forecasting/view.html', forecast=forecast)
    
    except Exception as e:
        logger.exception(e)
        flash('Error loading forecast.', 'danger')
        return redirect(url_for('forecasting.list_forecasts'))
