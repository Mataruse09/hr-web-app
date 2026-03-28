from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session,
)
import bcrypt
from models import user_model

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        user = user_model.get_by_username(username)

        if not user:
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('login.html')

        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('login.html')

        # Successful login — store minimal info in session
        session.permanent = True
        session['user_id']     = user['id']
        session['company_id']  = user['company_id']
        session['username']    = user['username']
        session['full_name']   = user['full_name']
        session['role']        = user['role']

        user_model.update_last_login(user['id'])
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))