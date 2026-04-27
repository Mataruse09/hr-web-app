"""
HR Management System — Application Factory
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for, render_template, Response
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
from routes.ai_analytics_routes import ai_analytics_bp
from routes.subscription_routes import subscription_bp
from routes.owner_routes import owner_bp


def setup_logging(app):
    """Configure application logging with rotation"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    log_level = logging.INFO
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # File handler with rotation (10MB max, keep 5 backup files)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Error file handler (separate file for errors)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configure app logger
    app.logger.setLevel(log_level)
    app.logger.handlers = []
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    
    # Prevent propagation to root logger (avoid duplicate logs)
    app.logger.propagate = False
    
    # Also configure root logger for other modules
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return app.logger


logger = setup_logging(Flask(__name__))

# Dynamic sitemap generation
def generate_sitemap():
    """Generate XML sitemap dynamically"""
    from datetime import datetime
    
    base_url = "https://hr-web-app-5.onrender.com"
    today = datetime.now().strftime("%Y-%m-%d")
    
    pages = [
        ("/", "1.0", "weekly"),
        ("/login", "0.9", "monthly"),
        ("/register", "0.9", "monthly"),
        ("/dashboard", "0.9", "weekly"),
        ("/employees", "0.9", "weekly"),
        ("/employees/add", "0.7", "monthly"),
        ("/attendance", "0.8", "weekly"),
        ("/attendance/logs", "0.7", "weekly"),
        ("/leave", "0.8", "weekly"),
        ("/payroll", "0.8", "monthly"),
        ("/ai-analytics", "0.8", "weekly"),
        ("/forecasting", "0.7", "weekly"),
        ("/attrition", "0.7", "monthly"),
        ("/compliance", "0.7", "monthly"),
        ("/appraisals", "0.7", "monthly"),
        ("/gamification", "0.6", "monthly"),
        ("/admin", "0.7", "monthly"),
    ]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, priority, changefreq in pages:
        xml += f'  <url>\n    <loc>{base_url}{path}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>\n'
    xml += '</urlset>'
    return xml


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    # Setup logging
    setup_logging(app)
    app.logger.info("Application starting up")
    
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
    app.register_blueprint(ai_analytics_bp, url_prefix='/ai-analytics')
    app.register_blueprint(subscription_bp, url_prefix='/subscription')
    app.register_blueprint(owner_bp)

    # ── Security Middleware ─────────────────────────────────────
    @app.before_request
    def check_blocked_ip():
        """Block suspicious IPs"""
        from flask import request, abort
        from models.db import query
        
        # Skip for owner routes
        if request.path.startswith('/owner'):
            return
        
        # Skip for static files (CSS, JS, images) to reduce DB load
        if request.path.startswith('/static'):
            return
        
        # Check if IP is blocked
        ip = request.remote_addr
        blocked = query("SELECT ip_address FROM blocked_ips WHERE ip_address = %s AND is_active = TRUE", (ip,), one=True)
        
        if blocked:
            logger.warning(f"Blocked IP attempted access: {ip}")
            abort(403)  # Forbidden
    @app.route('/sitemap.xml')
    def sitemap():
        """Serve dynamic sitemap"""
        xml = generate_sitemap()
        return Response(xml, mimetype='application/xml')

    # ── Legal Pages Routes ───────────────────────────────────────
    @app.route('/terms')
    def terms():
        """Terms and Conditions page"""
        return render_template('terms_conditions.html')

    @app.route('/privacy')
    def privacy():
        """Privacy Policy page"""
        return render_template('privacy_policy.html')

    @app.route('/policies')
    def policies():
        """Policies & Guidelines page"""
        return render_template('policies.html')

    # ── Global template context - make company available to all templates ──
    @app.before_request
    def add_company_to_template():
        from flask import g, session
        from models.company_model import get_by_id
        company_id = session.get('company_id')
        if company_id:
            g.company = get_by_id(company_id)
            # Add subscription context
            from services.subscription_service import add_subscription_context, get_all_features_with_status
            add_subscription_context()
            # Pass all features with their status for template use
            g.all_features = get_all_features_with_status(company_id)
            # Add theme settings for custom branding
            from services.settings_service import get_all_settings
            settings = get_all_settings(company_id)
            g.theme = {
                'primary': settings.get('theme_primary_color', '#1a2b4a'),
                'secondary': settings.get('theme_secondary_color', '#3498db'),
                'background': settings.get('theme_background_color', '#ecf0f1'),
                'accent': settings.get('theme_accent_color', '#e74c3c'),
            }
            g.company_logo = settings.get('company_logo_url', '')
            g.company_branding = settings.get('company_branding', 'MatinexHR')
        else:
            g.company = None
            g.subscription = {'status': 'none', 'plan_name': 'Free', 'features': []}
            g.features = []
            g.can_access_ai = False
            g.can_access_forecasting = False
            g.can_access_gamification = False
            g.can_access_compliance = False
            g.can_access_payroll = False
            g.can_access_appraisals = False
            g.all_features = []
            # Default theme for non-logged in users
            g.theme = {
                'primary': '#1a2b4a',
                'secondary': '#3498db',
                'background': '#ecf0f1',
                'accent': '#e74c3c',
            }
            g.company_logo = ''
            g.company_branding = 'MatinexHR'

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
        """, full_name='Guest', role='Guest', company_name='MatinexHR')

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"500 - Internal Server Error: {e}")
        return render_template('base.html', page_title='500', content="""
            <div class="section-card text-center">
                <h2>500 - Server Error</h2>
                <p>Something went wrong. Please try again later.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """, full_name='Guest', role='Guest', company_name='MatinexHR')

    @app.errorhandler(403)
    def forbidden(e):
        logger.warning(f"403 - Forbidden access: {e}")
        return render_template('base.html', page_title='403', content="""
            <div class="section-card text-center">
                <h2>403 - Access Denied</h2>
                <p>You don't have permission to access this resource.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """, full_name='Guest', role='Guest', company_name='MatinexHR')

    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"400 - Bad Request: {e}")
        return render_template('base.html', page_title='400', content="""
            <div class="section-card text-center">
                <h2>400 - Bad Request</h2>
                <p>Invalid request. Please check your input.</p>
                <a href="/" class="btn btn-primary">Go to Dashboard</a>
            </div>
        """, full_name='Guest', role='Guest', company_name='MatinexHR')

    # ── Favicon route to prevent 404 errors ───────────────────────
    @app.route('/favicon.ico')
    def favicon():
        from flask import send_from_directory
        import os
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
        return send_from_directory(static_folder, 'img/branding/favicon-64x64.png', mimetype='image/png')

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