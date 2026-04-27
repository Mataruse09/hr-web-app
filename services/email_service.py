"""
Email Service - Handle all email notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_HOST') or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SMTP_USER') or os.getenv('SENDER_EMAIL', 'noreply@hrapp.com')
SENDER_PASSWORD = os.getenv('SMTP_PASS') or os.getenv('SENDER_PASSWORD', '')
SUPPORT_EMAIL = 'tinashemataruse226@gmail.com'


def send_email(recipient_email: str, subject: str, body: str, is_html: bool = False):
    """Send an email to a recipient."""
    try:
        # Validate configuration
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            logger.error(f"❌ Email configuration incomplete: SENDER_EMAIL={bool(SENDER_EMAIL)}, SENDER_PASSWORD={bool(SENDER_PASSWORD)}")
            return False
            
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
        logger.error(f"❌ Email send failed to {recipient_email} ({type(e).__name__}): {e}")
        return False


def send_admin_registration_email(admin_name: str, admin_email: str, company_name: str):
    """Send welcome email to newly registered admin."""
    subject = f"Welcome to MatinexHR - {company_name}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">🎉 Welcome to MatinexHR, {admin_name}!</h2>
            </div>
            
            <p>Thank you for registering <strong>{company_name}</strong> with <strong>MatinexHR</strong>.</p>
            
            <p>We are excited to help you manage your HR operations efficiently and professionally.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1a237e;">📋 Getting Started:</h4>
                <ul style="margin-bottom: 0;">
                    <li>Access the admin dashboard to manage employees</li>
                    <li>Configure company settings and branding</li>
                    <li>Set up departments and roles</li>
                    <li>Manage attendance, payroll, and leave</li>
                </ul>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0; color: #856404;">🔐 Security Notice:</h4>
                <ul style="margin-bottom: 0;">
                    <li>Your password reset link is <strong>valid for only 30 minutes</strong></li>
                    <li>Each reset link can be used <strong>only once</strong></li>
                    <li>If you did not request this account, please contact us immediately</li>
                </ul>
            </div>
            
            <h4>Need Help?</h4>
            <p>For any queries or support, please contact us:</p>
            <p><strong>Email:</strong> <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>MatinexHR Team</strong><br>
                Professional HR Management System<br>
                <em>This is an automated message. Please do not reply to this email.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, body, is_html=True)


def send_password_reset_email(user_name: str, user_email: str, company_name: str, reset_link: str):
    """Send password reset email with security warnings."""
    subject = f"Password Reset Request - {company_name} - MatinexHR"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">🔐 Password Reset Request</h2>
            </div>
            
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>We received a request to reset your password for <strong>{company_name}</strong> on MatinexHR.</p>
            
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h4 style="margin-top: 0; color: #721c24;">⚠️ Important Security Information:</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>This link expires in 30 minutes</strong></li>
                    <li><strong>This link can only be used once</strong></li>
                    <li>After using this link, you will need to request a new one for future resets</li>
                </ul>
            </div>
            
            <p>Click the button below to reset your password:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: #1a237e; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
            </div>
            
            <p style="font-size: 14px; color: #6c757d;">Or copy and paste this link in your browser:<br>
            <span style="word-break: break-all; font-size: 12px;">{reset_link}</span></p>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0; color: #856404;">🛡️ Security Alert:</h4>
                <p style="margin-bottom: 0;">If you did not request a password reset, please <strong>ignore this email</strong> and contact your company administrator immediately at <strong>{SUPPORT_EMAIL}</strong>.</p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                <strong>MatinexHR Team</strong><br>
                Professional HR Management System<br>
                <em>This is an automated message. Please do not reply to this email.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(user_email, subject, body, is_html=True)


def send_employee_added_email(employee_name: str, employee_email: str, company_name: str, username: str, temp_password: str = None):
    """Send notification email to newly added employee with security info."""
    subject = f"Welcome to {company_name} - MatinexHR"
    
    password_section = f"""
    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
        <h4 style="margin-top: 0; color: #721c24;">🔐 Important Security Information:</h4>
        <ul style="margin-bottom: 0;">
            <li><strong>Your password reset link expires in 30 minutes</strong></li>
            <li><strong>Each reset link can only be used once</strong></li>
            <li>Please change your password after your first login</li>
        </ul>
    </div>
    
    <h3>Your Login Credentials:</h3>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <p style="margin: 5px 0;"><strong>Username:</strong> {username}</p>
        <p style="margin: 5px 0;"><strong>Temporary Password:</strong> {temp_password}</p>
    </div>
    """ if temp_password else ""
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #218838 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">🎉 Welcome to {company_name}, {employee_name}!</h2>
            </div>
            
            <p>Welcome to our team! You have been added to <strong>{company_name}</strong> on MatinexHR.</p>
            
            {password_section}
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1a237e;">📋 Your Portal Features:</h4>
                <ul style="margin-bottom: 0;">
                    <li>View your personal profile and documents</li>
                    <li>Track your attendance</li>
                    <li>Request and manage leave</li>
                    <li>View payroll information</li>
                </ul>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0; color: #856404;">🛡️ Security Notice:</h4>
                <p style="margin-bottom: 0;">If you do not recognize this email or were not added to {company_name}, please report this immediately to your company administrator or contact us at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            </div>
            
            <h4>Support:</h4>
            <p>For any assistance, contact: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>MatinexHR Team</strong><br>
                <em>This is an automated message. Please do not reply to this email.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(employee_email, subject, body, is_html=True)


def send_subscription_confirmation_email(admin_name: str, admin_email: str, company_name: str, plan_name: str):
    """Send email confirmation when admin subscribes/upgrades."""
    subject = f"✅ Subscription Confirmed - {plan_name} Plan - {company_name}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #218838 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">✅ Subscription Confirmed!</h2>
            </div>
            
            <p>Hello <strong>{admin_name}</strong>,</p>
            
            <p>Your subscription to the <strong>{plan_name}</strong> plan has been successfully confirmed for <strong>{company_name}</strong>.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1a237e;">📝 Subscription Details:</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Plan:</strong> {plan_name}</li>
                    <li><strong>Status:</strong> Active</li>
                    <li><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
                </ul>
            </div>
            
            <p>You can now access all features included in your plan.</p>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <h4 style="margin-top: 0; color: #856404;">🔐 Security Reminder:</h4>
                <ul style="margin-bottom: 0;">
                    <li>Password reset links expire in 30 minutes</li>
                    <li>Each reset link can only be used once</li>
                    <li>If you notice any suspicious activity, contact us immediately</li>
                </ul>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>MatinexHR Team</strong><br>
                Professional HR Management System<br>
                <em>This is an automated message. Please do not reply to this email.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, body, is_html=True)


def send_subscription_notification_to_owner(admin_name: str, admin_email: str, company_name: str, plan_name: str):
    """Send notification to the owner (tinashemataruse226@gmail.com) when a company subscribes."""
    subject = f"📢 New Subscription - {company_name} - {plan_name} Plan"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #6f42c1 0%, #5a32a3 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">📢 New Subscription Notification</h2>
            </div>
            
            <p>Hello Owner,</p>
            
            <p>A new company has subscribed to a <strong>{plan_name}</strong> plan.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1a237e;">🏢 Company Details:</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>Company Name:</strong> {company_name}</li>
                    <li><strong>Admin Name:</strong> {admin_name}</li>
                    <li><strong>Admin Email:</strong> {admin_email}</li>
                    <li><strong>Plan:</strong> {plan_name}</li>
                    <li><strong>Subscription Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                <strong>MatinexHR System</strong><br>
                Automated Notification<br>
                <em>This is an automated message.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send to the owner
    return send_email(SUPPORT_EMAIL, subject, body, is_html=True)


def send_team_notification_email(admin_name: str, admin_email: str, company_name: str, role: str, action: str = "added"):
    """Send notification to admins, CHRO, Manager, HR when they are added or updated."""
    subject = f"📢 You have been {action} to {company_name} - MatinexHR"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px;">
                <h2 style="margin: 0;">📢 Access Notification</h2>
            </div>
            
            <p>Hello <strong>{admin_name}</strong>,</p>
            
            <p>You have been <strong>{action}</strong> to <strong>{company_name}</strong> on MatinexHR as a <strong>{role}</strong>.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1a237e;">📝 Your Role:</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>Role:</strong> {role}</li>
                    <li><strong>Company:</strong> {company_name}</li>
                    <li><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</li>
                </ul>
            </div>
            
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545;">
                <h4 style="margin-top: 0; color: #721c24;">🔐 Important Security Information:</h4>
                <ul style="margin-bottom: 0;">
                    <li><strong>Password reset links expire in 30 minutes</strong></li>
                    <li><strong>Each reset link can only be used once</strong></li>
                    <li>If you did not expect this email, please contact your administrator immediately</li>
                </ul>
            </div>
            
            <p>You can now log in to access your dashboard.</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="font-size: 12px; color: #7f8c8d;">
                Best regards,<br>
                <strong>MatinexHR Team</strong><br>
                <em>This is an automated message. Please do not reply to this email.</em>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(admin_email, subject, body, is_html=True)
