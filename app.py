"""
HR Management System — Application Factory
"""
import logging
from flask import Flask, redirect, url_for, render_template
from datetime import timedelta
from config.settings import Config
from models.db import init_db
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

    # Session timeout (30 minutes)
    app.permanent_session_lifetime = timedelta(minutes=30)

    init_db(app)

    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
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

    # ── Global Error Handlers ───────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        logger.warning("404 - Page not found")
        return render_template('base.html', page_title='404', content="""
            <div class="section-card text-center">
                <h2>404 - Page Not Found</h2>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """)

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"500 - Internal Server Error: {e}")
        return render_template('base.html', page_title='500', content="""
            <div class="section-card text-center">
                <h2>500 - Server Error</h2>
                <p>Something went wrong. Please try again later.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """)

    @app.errorhandler(403)
    def forbidden(e):
        logger.warning(f"403 - Forbidden access: {e}")
        return render_template('base.html', page_title='403', content="""
            <div class="section-card text-center">
                <h2>403 - Access Denied</h2>
                <p>You don't have permission to access this resource.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """)

    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"400 - Bad Request: {e}")
        return render_template('base.html', page_title='400', content="""
            <div class="section-card text-center">
                <h2>400 - Bad Request</h2>
                <p>Invalid request. Please check your input.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """)

    # ── Favicon route to prevent 404 errors ───────────────────────
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        import os
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        return send_from_directory(static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app


import os

app = create_app()

# ── Google Site Verification Route ─────────────
from flask import send_from_directory, Response

@app.route('/googledabc1683b170bb18.html')
def google_verification():
    return send_from_directory('.', 'googledabc1683b170bb18.html')

# ── Robots.txt Route ─────────────
@app.route('/robots.txt')
def robots_txt():
    return Response("User-agent: *\nAllow: /\n\nSitemap: https://hr-web-app-5.onrender.com/sitemap.xml", mimetype='text/plain')

# ── Sitemap.xml Route ─────────────
@app.route('/sitemap.xml')
def sitemap_xml():
    return Response('''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://hr-web-app-5.onrender.com/</loc>
    <lastmod>2026-04-24</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://hr-web-app-5.onrender.com/landing</loc>
    <lastmod>2026-04-24</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://hr-web-app-5.onrender.com/auth/login</loc>
    <lastmod>2026-04-24</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://hr-web-app-5.onrender.com/auth/register-company</loc>
    <lastmod>2026-04-24</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>''', mimetype='application/xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))