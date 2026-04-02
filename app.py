"""
HR Management System — Application Factory
"""
from flask import Flask, redirect, url_for
from config.settings import Config
from models.db import init_db
from models.user_model import seed_roles
from routes.auth_routes       import auth_bp
from routes.dashboard_routes  import dashboard_bp
from routes.employee_routes   import employee_bp
from routes.attendance_routes import attendance_bp
from routes.leave_routes      import leave_bp
from routes.payroll_routes    import payroll_bp
from routes.admin_routes      import admin_bp


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    init_db(app)
    with app.app_context():
        seed_roles()

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(dashboard_bp)                       # handles '/' and '/dashboard'
    app.register_blueprint(employee_bp,   url_prefix='/employees')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(leave_bp,      url_prefix='/leave')
    app.register_blueprint(payroll_bp,    url_prefix='/payroll')
    app.register_blueprint(admin_bp,      url_prefix='/admin')

    @app.errorhandler(404)
    def not_found(_):
        return redirect(url_for('dashboard.index'))

    return app


import os

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))