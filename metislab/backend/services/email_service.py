import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from flask import current_app
from backend.models.user import User
from backend.models.project_request import ProjectRequest

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = current_app.config.get('SMTP_PORT', 587)
        self.smtp_username = current_app.config.get('SMTP_USERNAME')
        self.smtp_password = current_app.config.get('SMTP_PASSWORD')
        self.from_email = current_app.config.get('FROM_EMAIL', 'noreply@metislab.edu')
        self.from_name = current_app.config.get('FROM_NAME', 'METIS Lab')

    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email to recipient"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Email not sent.")
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_new_request_notification(self, request_obj):
        """Send notification to admins about new request"""
        try:
            # Get all admin users
            admins = User.query.filter_by(role='admin', is_active=True).all()
            
            if not admins:
                logger.warning("No admin users found for new request notification")
                return False

            subject = f"New Project Request Submitted - #{request_obj.id}"
            
            # Create HTML content
            html_content = self._get_new_request_email_template(request_obj)
            text_content = self._get_new_request_email_text(request_obj)

            # Send to all admins
            success_count = 0
            for admin in admins:
                if self.send_email(admin.email, subject, html_content, text_content):
                    success_count += 1

            logger.info(f"New request notification sent to {success_count}/{len(admins)} admins")
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send new request notification: {str(e)}")
            return False

    def send_approval_notification(self, request_obj, approved_by):
        """Send approval notification to user"""
        try:
            user = User.query.get(request_obj.user_id)
            if not user:
                logger.error(f"User not found for request {request_obj.id}")
                return False

            subject = f"Project Request Approved - #{request_obj.id}"
            
            # Create HTML content
            html_content = self._get_approval_email_template(request_obj, approved_by)
            text_content = self._get_approval_email_text(request_obj, approved_by)

            return self.send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send approval notification: {str(e)}")
            return False

    def send_rejection_notification(self, request_obj, rejected_by, reason):
        """Send rejection notification to user"""
        try:
            user = User.query.get(request_obj.user_id)
            if not user:
                logger.error(f"User not found for request {request_obj.id}")
                return False

            subject = f"Project Request Rejected - #{request_obj.id}"
            
            # Create HTML content
            html_content = self._get_rejection_email_template(request_obj, rejected_by, reason)
            text_content = self._get_rejection_email_text(request_obj, rejected_by, reason)

            return self.send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send rejection notification: {str(e)}")
            return False

    def _get_new_request_email_template(self, request_obj):
        """Generate HTML template for new request notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Project Request</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .request-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>METIS Lab</h1>
                    <h2>New Project Request Submitted</h2>
                </div>
                <div class="content">
                    <p>A new project request has been submitted and requires your attention.</p>
                    
                    <div class="request-details">
                        <h3>Request Details</h3>
                        <p><strong>Request ID:</strong> #{request_obj.id}</p>
                        <p><strong>Project Title:</strong> {request_obj.project_title}</p>
                        <p><strong>Submitted By:</strong> {user.full_name if user else 'Unknown'} ({user.email if user else 'N/A'})</p>
                        <p><strong>Department:</strong> {user.department.value if user and user.department else 'N/A'}</p>
                        <p><strong>Priority:</strong> {request_obj.priority.value.title()}</p>
                        <p><strong>Submitted At:</strong> {request_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Status:</strong> {request_obj.status.value.replace('_', ' ').title()}</p>
                    </div>
                    
                    <div class="request-details">
                        <h3>Project Description</h3>
                        <p>{request_obj.description[:200]}{'...' if len(request_obj.description) > 200 else ''}</p>
                    </div>
                    
                    <p style="text-align: center; margin: 20px 0;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/admin/requests/{request_obj.id}" class="btn">
                            Review Request
                        </a>
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated notification from METIS Lab Management System.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_new_request_email_text(self, request_obj):
        """Generate text version for new request notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        METIS Lab - New Project Request Submitted
        
        A new project request has been submitted and requires your attention.
        
        Request Details:
        - Request ID: #{request_obj.id}
        - Project Title: {request_obj.project_title}
        - Submitted By: {user.full_name if user else 'Unknown'} ({user.email if user else 'N/A'})
        - Department: {user.department.value if user and user.department else 'N/A'}
        - Priority: {request_obj.priority.value.title()}
        - Submitted At: {request_obj.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
        - Status: {request_obj.status.value.replace('_', ' ').title()}
        
        Project Description:
        {request_obj.description[:200]}{'...' if len(request_obj.description) > 200 else ''}
        
        Please review the request in the admin dashboard.
        
        This is an automated notification from METIS Lab Management System.
        """

    def _get_approval_email_template(self, request_obj, approved_by):
        """Generate HTML template for approval notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Project Request Approved</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .request-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .credentials {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #27ae60; }}
                .footer {{ text-align: center; padding: 20px; color: #666; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Request Approved!</h1>
                    <h2>METIS Lab Access Granted</h2>
                </div>
                <div class="content">
                    <p>Dear {user.full_name if user else 'User'},</p>
                    
                    <p>Great news! Your project request has been approved and you now have access to the METIS Lab resources.</p>
                    
                    <div class="request-details">
                        <h3>Request Details</h3>
                        <p><strong>Request ID:</strong> #{request_obj.id}</p>
                        <p><strong>Project Title:</strong> {request_obj.project_title}</p>
                        <p><strong>Approved By:</strong> {approved_by.full_name if approved_by else 'Administrator'}</p>
                        <p><strong>Approved At:</strong> {request_obj.approved_at.strftime('%Y-%m-%d %H:%M:%S') if request_obj.approved_at else 'N/A'}</p>
                    </div>
                    
                    <div class="credentials">
                        <h3>🔑 Your Access Credentials</h3>
                        <p><strong>Lab Access:</strong> Granted</p>
                        <p><strong>Computational Resources:</strong> Available</p>
                        <p><strong>Data Storage:</strong> Allocated</p>
                        <p><strong>Support Contact:</strong> metis-support@university.edu</p>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Access the METIS Lab dashboard to view your allocated resources</li>
                        <li>Review the lab usage guidelines and policies</li>
                        <li>Contact the lab support team if you need assistance</li>
                        <li>Begin your project work using the approved resources</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 20px 0;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/dashboard" class="btn">
                            Access Dashboard
                        </a>
                    </p>
                </div>
                <div class="footer">
                    <p>Congratulations on your approved project! We look forward to seeing your research results.</p>
                    <p>This is an automated notification from METIS Lab Management System.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_approval_email_text(self, request_obj, approved_by):
        """Generate text version for approval notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        METIS Lab - Project Request Approved
        
        Dear {user.full_name if user else 'User'},
        
        Great news! Your project request has been approved and you now have access to the METIS Lab resources.
        
        Request Details:
        - Request ID: #{request_obj.id}
        - Project Title: {request_obj.project_title}
        - Approved By: {approved_by.full_name if approved_by else 'Administrator'}
        - Approved At: {request_obj.approved_at.strftime('%Y-%m-%d %H:%M:%S') if request_obj.approved_at else 'N/A'}
        
        Your Access Credentials:
        - Lab Access: Granted
        - Computational Resources: Available
        - Data Storage: Allocated
        - Support Contact: metis-support@university.edu
        
        Next Steps:
        1. Access the METIS Lab dashboard to view your allocated resources
        2. Review the lab usage guidelines and policies
        3. Contact the lab support team if you need assistance
        4. Begin your project work using the approved resources
        
        Congratulations on your approved project! We look forward to seeing your research results.
        
        This is an automated notification from METIS Lab Management System.
        """

    def _get_rejection_email_template(self, request_obj, rejected_by, reason):
        """Generate HTML template for rejection notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Project Request Rejected</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #e74c3c; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .request-details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .rejection-reason {{ background-color: #fdf2f2; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #e74c3c; }}
                .footer {{ text-align: center; padding: 20px; color: #666; }}
                .btn {{ display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Request Rejected</h1>
                    <h2>METIS Lab Project Request</h2>
                </div>
                <div class="content">
                    <p>Dear {user.full_name if user else 'User'},</p>
                    
                    <p>We regret to inform you that your project request has been rejected. Please review the details below.</p>
                    
                    <div class="request-details">
                        <h3>Request Details</h3>
                        <p><strong>Request ID:</strong> #{request_obj.id}</p>
                        <p><strong>Project Title:</strong> {request_obj.project_title}</p>
                        <p><strong>Rejected By:</strong> {rejected_by.full_name if rejected_by else 'Administrator'}</p>
                        <p><strong>Rejected At:</strong> {request_obj.rejected_at.strftime('%Y-%m-%d %H:%M:%S') if request_obj.rejected_at else 'N/A'}</p>
                    </div>
                    
                    <div class="rejection-reason">
                        <h3>Rejection Reason</h3>
                        <p>{reason}</p>
                    </div>
                    
                    <p><strong>What's Next?</strong></p>
                    <ul>
                        <li>Review the rejection reason and address any concerns</li>
                        <li>You may submit a new request with the necessary modifications</li>
                        <li>Contact the admin team for clarification if needed</li>
                        <li>Consider discussing your project requirements with faculty advisors</li>
                    </ul>
                    
                    <p style="text-align: center; margin: 20px 0;">
                        <a href="{current_app.config.get('BASE_URL', 'http://localhost:5000')}/dashboard" class="btn">
                            Submit New Request
                        </a>
                    </p>
                    
                    <p><strong>Need Help?</strong></p>
                    <p>If you have questions about this rejection or need assistance with your project proposal, please contact:</p>
                    <p>Email: metis-admin@university.edu<br>
                    Phone: +1 (555) 123-4567</p>
                </div>
                <div class="footer">
                    <p>We encourage you to resubmit your request with the necessary improvements.</p>
                    <p>This is an automated notification from METIS Lab Management System.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_rejection_email_text(self, request_obj, rejected_by, reason):
        """Generate text version for rejection notification"""
        user = User.query.get(request_obj.user_id)
        return f"""
        METIS Lab - Project Request Rejected
        
        Dear {user.full_name if user else 'User'},
        
        We regret to inform you that your project request has been rejected. Please review the details below.
        
        Request Details:
        - Request ID: #{request_obj.id}
        - Project Title: {request_obj.project_title}
        - Rejected By: {rejected_by.full_name if rejected_by else 'Administrator'}
        - Rejected At: {request_obj.rejected_at.strftime('%Y-%m-%d %H:%M:%S') if request_obj.rejected_at else 'N/A'}
        
        Rejection Reason:
        {reason}
        
        What's Next?
        1. Review the rejection reason and address any concerns
        2. You may submit a new request with the necessary modifications
        3. Contact the admin team for clarification if needed
        4. Consider discussing your project requirements with faculty advisors
        
        Need Help?
        If you have questions about this rejection or need assistance with your project proposal, please contact:
        Email: metis-admin@university.edu
        Phone: +1 (555) 123-4567
        
        We encourage you to resubmit your request with the necessary improvements.
        
        This is an automated notification from METIS Lab Management System.
        """
