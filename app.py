"""
HR Management System — Application Factory
"""
import logging
from flask import Flask, redirect, url_for
from datetime import timedelta  # ✅ ADDED
from config.settings import Config
from models.db import init_db  # MySQL connection handler
from models.user_model import seed_roles
from routes.auth_routes       import auth_bp
from routes.dashboard_routes  import dashboard_bp
from routes.employee_routes   import employee_bp
from routes.attendance_routes import attendance_bp
from routes.leave_routes      import leave_bp
from routes.payroll_routes    import payroll_bp
from routes.admin_routes      import admin_bp
from routes.appraisal_routes  import appraisal_bp
from routes.gamification_routes import gamification_bp
from routes.forecasting_routes import forecasting_bp
from routes.attrition_routes  import attrition_bp
from routes.compliance_routes import compliance_bp

logger = logging.getLogger(__name__)


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # ✅ SESSION TIMEOUT (30 minutes)
    app.permanent_session_lifetime = timedelta(minutes=30)

    init_db(app)
    with app.app_context():
        try:
            seed_roles()
            logger.info("✅ Database roles seeded successfully")
        except Exception as e:
            logger.warning("⚠️  Could not seed database roles (DB may not be available): %s", e)

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(dashboard_bp)                       # handles '/' and '/dashboard'
    app.register_blueprint(employee_bp,   url_prefix='/employees')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(leave_bp,      url_prefix='/leave')
    app.register_blueprint(payroll_bp,    url_prefix='/payroll')
    app.register_blueprint(admin_bp,      url_prefix='/admin')
    app.register_blueprint(appraisal_bp,  url_prefix='/appraisals')
    app.register_blueprint(gamification_bp, url_prefix='/gamification')
    app.register_blueprint(forecasting_bp, url_prefix='/forecasting')
    app.register_blueprint(attrition_bp,  url_prefix='/attrition')
    app.register_blueprint(compliance_bp, url_prefix='/compliance')

    @app.errorhandler(404)
    def not_found(_):
        return redirect(url_for('dashboard.index'))

    return app


import os

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))