"""
Email Service - Handle all email notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'noreply@hrapp.com')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
SUPPORT_EMAIL = 'tinashemataruse226@gmail.com'


def send_email(recipient_email: str, subject: str, body: str, is_html: bool = False):
    """Send an email to a recipient."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        mime_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, mime_type))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Email send failed to {recipient_email}: {e}")
        return False


def send_admin_registration_email(admin_name: str, admin_email: str, company_name: str):
    """Send welcome email to newly registered admin."""
    subject = f"Welcome to WorkZen HR - {company_name}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Welcome to WorkZen HR, {admin_name}!</h2>
            
            <p>Thank you for registering <strong>{company_name}</strong> with <strong>WorkZen HR</strong>.</p>
            
            <p>We are excited to help you manage your HR operations efficiently and professionally.</p>
            
            <h3>Getting Started:</h3>
            <ul>
                <li>Access the admin dashboard to manage employees</li>
                <li>Configure company settings and branding</li>
                <li>Set up departments and roles</li>
                <li>Manage attendance, payroll, and leave</li>
            </ul>
            
            <h3>Need Help?</h3>
            <p>For any queries or support, please contact us:</p>
            <p><strong>Email:</strong> <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>WorkZen HR Team</strong><br>
                Professional HR Management System
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, body, is_html=True)


def send_employee_added_email(employee_name: str, employee_email: str, company_name: str, username: str, temp_password: str = None):
    """Send notification email to newly added employee."""
    subject = f"Welcome to {company_name} - WorkZen HR"
    
    password_section = f"""
    <h3>Your Login Credentials:</h3>
    <p>
        <strong>Username:</strong> {username}<br>
        <strong>Temporary Password:</strong> {temp_password}
    </p>
    <p style="color: #e74c3c;">⚠️ Please change your password after your first login.</p>
    """ if temp_password else ""
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Welcome to {company_name}, {employee_name}!</h2>
            
            <p>Welcome to our team! You have been added to <strong>{company_name}</strong> on WorkZen HR.</p>
            
            {password_section}
            
            <h3>Your Portal Features:</h3>
            <ul>
                <li>View your personal profile and documents</li>
                <li>Track your attendance</li>
                <li>Request and manage leave</li>
                <li>View payroll information</li>
            </ul>
            
            <h3>Support:</h3>
            <p>For any assistance, contact: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>WorkZen HR Team</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(employee_email, subject, body, is_html=True)
