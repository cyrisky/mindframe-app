"""Email service for notifications and communication"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pathlib import Path
import jinja2
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str = None
    from_name: str = None


@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: str = 'application/octet-stream'


@dataclass
class EmailTemplate:
    """Email template"""
    name: str
    subject: str
    html_content: str
    text_content: str = None
    variables: List[str] = None


class EmailService:
    """Service for sending emails and managing email templates"""
    
    def __init__(self):
        self.config = None
        self.templates = {}
        self.template_engine = None
        self._initialized = False
    
    def initialize(self, config: EmailConfig = None) -> bool:
        """Initialize email service"""
        try:
            # Use provided config or load from environment
            if config:
                self.config = config
            else:
                self.config = EmailConfig(
                    smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    smtp_port=int(os.getenv('SMTP_PORT', '587')),
                    username=os.getenv('SMTP_USERNAME', ''),
                    password=os.getenv('SMTP_PASSWORD', ''),
                    use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
                    use_ssl=os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
                    from_email=os.getenv('SMTP_FROM_EMAIL', ''),
                    from_name=os.getenv('SMTP_FROM_NAME', 'Mindframe App')
                )
            
            # Set default from_email if not provided
            if not self.config.from_email:
                self.config.from_email = self.config.username
            
            # Initialize Jinja2 template engine
            self.template_engine = jinja2.Environment(
                loader=jinja2.DictLoader({}),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
            
            # Load default templates
            self._load_default_templates()
            
            self._initialized = True
            logger.info(f"Email service initialized with SMTP server: {self.config.smtp_server}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform email service health check"""
        try:
            health_info = {
                "status": "healthy",
                "smtp_server": self.config.smtp_server if self.config else None,
                "smtp_port": self.config.smtp_port if self.config else None,
                "from_email": self.config.from_email if self.config else None,
                "templates_loaded": len(self.templates),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test SMTP connection
            if self.config:
                try:
                    with self._get_smtp_connection() as smtp:
                        smtp.noop()
                    health_info["smtp_connection"] = "success"
                except Exception as e:
                    health_info["smtp_connection"] = "failed"
                    health_info["smtp_error"] = str(e)
                    health_info["status"] = "degraded"
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Email health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_smtp_connection(self):
        """Get SMTP connection"""
        if self.config.use_ssl:
            smtp = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port)
        else:
            smtp = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.use_tls:
                smtp.starttls()
        
        if self.config.username and self.config.password:
            smtp.login(self.config.username, self.config.password)
        
        return smtp
    
    def _load_default_templates(self):
        """Load default email templates"""
        # Welcome email template
        self.templates['welcome'] = EmailTemplate(
            name='welcome',
            subject='Welcome to Mindframe App',
            html_content="""
            <html>
            <body>
                <h2>Welcome to Mindframe App, {{ user_name }}!</h2>
                <p>Thank you for joining our psychological report generation platform.</p>
                <p>Your account has been successfully created with the email: <strong>{{ user_email }}</strong></p>
                <p>You can now start creating professional psychological reports.</p>
                <br>
                <p>Best regards,<br>The Mindframe Team</p>
            </body>
            </html>
            """,
            text_content="""
            Welcome to Mindframe App, {{ user_name }}!
            
            Thank you for joining our psychological report generation platform.
            Your account has been successfully created with the email: {{ user_email }}
            
            You can now start creating professional psychological reports.
            
            Best regards,
            The Mindframe Team
            """,
            variables=['user_name', 'user_email']
        )
        
        # Password reset template
        self.templates['password_reset'] = EmailTemplate(
            name='password_reset',
            subject='Password Reset Request',
            html_content="""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello {{ user_name }},</p>
                <p>We received a request to reset your password for your Mindframe App account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{{ reset_link }}">Reset Password</a></p>
                <p>This link will expire in {{ expiry_hours }} hours.</p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The Mindframe Team</p>
            </body>
            </html>
            """,
            text_content="""
            Password Reset Request
            
            Hello {{ user_name }},
            
            We received a request to reset your password for your Mindframe App account.
            
            Click the link below to reset your password:
            {{ reset_link }}
            
            This link will expire in {{ expiry_hours }} hours.
            
            If you didn't request this password reset, please ignore this email.
            
            Best regards,
            The Mindframe Team
            """,
            variables=['user_name', 'reset_link', 'expiry_hours']
        )
        
        # Report generated notification
        self.templates['report_generated'] = EmailTemplate(
            name='report_generated',
            subject='Your Psychological Report is Ready',
            html_content="""
            <html>
            <body>
                <h2>Your Report is Ready</h2>
                <p>Hello {{ user_name }},</p>
                <p>Your psychological report for <strong>{{ client_name }}</strong> has been successfully generated.</p>
                <p><strong>Report Details:</strong></p>
                <ul>
                    <li>Report ID: {{ report_id }}</li>
                    <li>Client: {{ client_name }}</li>
                    <li>Generated: {{ generated_date }}</li>
                    <li>Pages: {{ page_count }}</li>
                </ul>
                <p>You can download your report from the dashboard or use the link below:</p>
                <p><a href="{{ download_link }}">Download Report</a></p>
                <br>
                <p>Best regards,<br>The Mindframe Team</p>
            </body>
            </html>
            """,
            text_content="""
            Your Report is Ready
            
            Hello {{ user_name }},
            
            Your psychological report for {{ client_name }} has been successfully generated.
            
            Report Details:
            - Report ID: {{ report_id }}
            - Client: {{ client_name }}
            - Generated: {{ generated_date }}
            - Pages: {{ page_count }}
            
            You can download your report from the dashboard or use the link below:
            {{ download_link }}
            
            Best regards,
            The Mindframe Team
            """,
            variables=['user_name', 'client_name', 'report_id', 'generated_date', 'page_count', 'download_link']
        )
        
        # Account locked notification
        self.templates['account_locked'] = EmailTemplate(
            name='account_locked',
            subject='Account Security Alert - Account Locked',
            html_content="""
            <html>
            <body>
                <h2>Account Security Alert</h2>
                <p>Hello {{ user_name }},</p>
                <p>Your Mindframe App account has been temporarily locked due to multiple failed login attempts.</p>
                <p><strong>Security Details:</strong></p>
                <ul>
                    <li>Failed attempts: {{ failed_attempts }}</li>
                    <li>Last attempt: {{ last_attempt_time }}</li>
                    <li>IP Address: {{ ip_address }}</li>
                </ul>
                <p>Your account will be automatically unlocked in {{ unlock_time }} minutes.</p>
                <p>If this wasn't you, please contact our support team immediately.</p>
                <br>
                <p>Best regards,<br>The Mindframe Security Team</p>
            </body>
            </html>
            """,
            text_content="""
            Account Security Alert
            
            Hello {{ user_name }},
            
            Your Mindframe App account has been temporarily locked due to multiple failed login attempts.
            
            Security Details:
            - Failed attempts: {{ failed_attempts }}
            - Last attempt: {{ last_attempt_time }}
            - IP Address: {{ ip_address }}
            
            Your account will be automatically unlocked in {{ unlock_time }} minutes.
            
            If this wasn't you, please contact our support team immediately.
            
            Best regards,
            The Mindframe Security Team
            """,
            variables=['user_name', 'failed_attempts', 'last_attempt_time', 'ip_address', 'unlock_time']
        )
        
        logger.info(f"Loaded {len(self.templates)} default email templates")
    
    def add_template(self, template: EmailTemplate):
        """Add email template"""
        self.templates[template.name] = template
        logger.info(f"Added email template: {template.name}")
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get email template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List available template names"""
        return list(self.templates.keys())
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render email template with variables"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        try:
            # Render subject
            subject_template = self.template_engine.from_string(template.subject)
            rendered_subject = subject_template.render(**variables)
            
            # Render HTML content
            html_template = self.template_engine.from_string(template.html_content)
            rendered_html = html_template.render(**variables)
            
            # Render text content if available
            rendered_text = None
            if template.text_content:
                text_template = self.template_engine.from_string(template.text_content)
                rendered_text = text_template.render(**variables)
            
            return {
                'subject': rendered_subject,
                'html': rendered_html,
                'text': rendered_text
            }
            
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    def send_email(self, 
                   to_emails: Union[str, List[str]],
                   subject: str,
                   html_content: str = None,
                   text_content: str = None,
                   attachments: List[EmailAttachment] = None,
                   cc_emails: List[str] = None,
                   bcc_emails: List[str] = None,
                   reply_to: str = None) -> bool:
        """Send email"""
        try:
            if not self.config:
                raise ValueError("Email service not initialized")
            
            # Ensure to_emails is a list
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>" if self.config.from_name else self.config.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.filename}'
                    )
                    msg.attach(part)
            
            # Prepare recipient list
            recipients = to_emails.copy()
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)
            
            # Send email
            with self._get_smtp_connection() as smtp:
                smtp.send_message(msg, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_template_email(self,
                           to_emails: Union[str, List[str]],
                           template_name: str,
                           variables: Dict[str, Any],
                           attachments: List[EmailAttachment] = None,
                           cc_emails: List[str] = None,
                           bcc_emails: List[str] = None) -> bool:
        """Send email using template"""
        try:
            # Render template
            rendered = self.render_template(template_name, variables)
            
            # Send email
            return self.send_email(
                to_emails=to_emails,
                subject=rendered['subject'],
                html_content=rendered['html'],
                text_content=rendered['text'],
                attachments=attachments,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails
            )
            
        except Exception as e:
            logger.error(f"Error sending template email: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        return self.send_template_email(
            to_emails=user_email,
            template_name='welcome',
            variables={
                'user_name': user_name,
                'user_email': user_email
            }
        )
    
    def send_password_reset_email(self, user_email: str, user_name: str, 
                                 reset_link: str, expiry_hours: int = 24) -> bool:
        """Send password reset email"""
        return self.send_template_email(
            to_emails=user_email,
            template_name='password_reset',
            variables={
                'user_name': user_name,
                'reset_link': reset_link,
                'expiry_hours': expiry_hours
            }
        )
    
    def send_report_notification(self, user_email: str, user_name: str,
                               client_name: str, report_id: str,
                               download_link: str, page_count: int = None) -> bool:
        """Send report generation notification"""
        return self.send_template_email(
            to_emails=user_email,
            template_name='report_generated',
            variables={
                'user_name': user_name,
                'client_name': client_name,
                'report_id': report_id,
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'page_count': page_count or 'N/A',
                'download_link': download_link
            }
        )
    
    def send_account_locked_notification(self, user_email: str, user_name: str,
                                       failed_attempts: int, ip_address: str,
                                       unlock_time: int) -> bool:
        """Send account locked notification"""
        return self.send_template_email(
            to_emails=user_email,
            template_name='account_locked',
            variables={
                'user_name': user_name,
                'failed_attempts': failed_attempts,
                'last_attempt_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': ip_address,
                'unlock_time': unlock_time
            }
        )
    
    def send_pdf_attachment(self, to_emails: Union[str, List[str]],
                           subject: str, message: str,
                           pdf_content: bytes, pdf_filename: str) -> bool:
        """Send email with PDF attachment"""
        attachment = EmailAttachment(
            filename=pdf_filename,
            content=pdf_content,
            content_type='application/pdf'
        )
        
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=f"<p>{message}</p>",
            text_content=message,
            attachments=[attachment]
        )
    
    def validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def bulk_send_email(self, email_list: List[Dict[str, Any]],
                       template_name: str, 
                       common_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send bulk emails with individual variables"""
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for email_data in email_list:
            try:
                # Merge common variables with individual variables
                variables = common_variables.copy() if common_variables else {}
                variables.update(email_data.get('variables', {}))
                
                success = self.send_template_email(
                    to_emails=email_data['email'],
                    template_name=template_name,
                    variables=variables
                )
                
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {email_data['email']}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error sending to {email_data.get('email', 'unknown')}: {str(e)}")
        
        logger.info(f"Bulk email completed: {results['sent']} sent, {results['failed']} failed")
        return results


# Global email service instance
email_service = EmailService()