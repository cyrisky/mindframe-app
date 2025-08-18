"""Email utilities for the mindframe application"""

import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, parseaddr
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import mimetypes
from email_validator import validate_email, EmailNotValidError


@dataclass
class EmailAddress:
    """Email address with optional display name"""
    email: str
    name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.name:
            return formataddr((self.name, self.email))
        return self.email
    
    @classmethod
    def from_string(cls, email_string: str) -> 'EmailAddress':
        """Create EmailAddress from string
        
        Args:
            email_string: Email string (e.g., 'John Doe <john@example.com>')
            
        Returns:
            EmailAddress: Parsed email address
        """
        name, email = parseaddr(email_string)
        return cls(email=email, name=name if name else None)


@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: Optional[str] = None
    
    def __post_init__(self):
        if not self.content_type:
            self.content_type, _ = mimetypes.guess_type(self.filename)
            if not self.content_type:
                self.content_type = 'application/octet-stream'


class EmailUtils:
    """Utility class for email operations"""
    
    # Email regex pattern (basic validation)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def validate_email_address(email: str) -> bool:
        """Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_email_list(emails: List[str]) -> Dict[str, List[str]]:
        """Validate list of email addresses
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dict: Dictionary with 'valid' and 'invalid' email lists
        """
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if EmailUtils.validate_email_address(email.strip()):
                valid_emails.append(email.strip())
            else:
                invalid_emails.append(email.strip())
        
        return {
            'valid': valid_emails,
            'invalid': invalid_emails
        }
    
    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """Extract domain from email address
        
        Args:
            email: Email address
            
        Returns:
            Optional[str]: Domain or None if invalid email
        """
        if not EmailUtils.validate_email_address(email):
            return None
        return email.split('@')[1].lower()
    
    @staticmethod
    def extract_username(email: str) -> Optional[str]:
        """Extract username from email address
        
        Args:
            email: Email address
            
        Returns:
            Optional[str]: Username or None if invalid email
        """
        if not EmailUtils.validate_email_address(email):
            return None
        return email.split('@')[0]
    
    @staticmethod
    def normalize_email(email: str) -> Optional[str]:
        """Normalize email address
        
        Args:
            email: Email address to normalize
            
        Returns:
            Optional[str]: Normalized email or None if invalid
        """
        if not EmailUtils.validate_email_address(email):
            return None
        
        # Convert to lowercase and strip whitespace
        normalized = email.strip().lower()
        
        # Handle Gmail-specific normalization
        username, domain = normalized.split('@')
        if domain in ['gmail.com', 'googlemail.com']:
            # Remove dots and plus addressing
            username = username.replace('.', '')
            if '+' in username:
                username = username.split('+')[0]
            domain = 'gmail.com'  # Normalize googlemail.com to gmail.com
        
        return f"{username}@{domain}"
    
    @staticmethod
    def is_disposable_email(email: str) -> bool:
        """Check if email is from a disposable email provider
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if disposable, False otherwise
        """
        # Common disposable email domains
        disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org',
            'throwaway.email', 'getnada.com', 'maildrop.cc'
        }
        
        domain = EmailUtils.extract_domain(email)
        return domain in disposable_domains if domain else False
    
    @staticmethod
    def create_mime_message(sender: Union[str, EmailAddress],
                          recipients: List[Union[str, EmailAddress]],
                          subject: str,
                          body: str,
                          html_body: Optional[str] = None,
                          attachments: Optional[List[EmailAttachment]] = None,
                          cc: Optional[List[Union[str, EmailAddress]]] = None,
                          bcc: Optional[List[Union[str, EmailAddress]]] = None) -> MIMEMultipart:
        """Create MIME message for email
        
        Args:
            sender: Sender email address
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: Optional list of attachments
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            MIMEMultipart: MIME message
        """
        msg = MIMEMultipart('alternative')
        
        # Set headers
        msg['From'] = str(sender)
        msg['To'] = ', '.join([str(recipient) for recipient in recipients])
        msg['Subject'] = subject
        
        if cc:
            msg['Cc'] = ', '.join([str(recipient) for recipient in cc])
        
        # Add text body
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Add HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Add attachments if provided
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
        
        return msg
    
    @staticmethod
    def create_attachment_from_file(file_path: Union[str, Path]) -> EmailAttachment:
        """Create email attachment from file
        
        Args:
            file_path: Path to file
            
        Returns:
            EmailAttachment: Email attachment object
        """
        file_path = Path(file_path)
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        return EmailAttachment(
            filename=file_path.name,
            content=content
        )
    
    @staticmethod
    def parse_email_list(email_string: str, delimiter: str = ',') -> List[str]:
        """Parse comma-separated email list
        
        Args:
            email_string: String containing multiple emails
            delimiter: Delimiter used to separate emails
            
        Returns:
            List[str]: List of email addresses
        """
        if not email_string:
            return []
        
        emails = [email.strip() for email in email_string.split(delimiter)]
        return [email for email in emails if email]
    
    @staticmethod
    def format_email_list(emails: List[Union[str, EmailAddress]], delimiter: str = ', ') -> str:
        """Format email list as string
        
        Args:
            emails: List of email addresses
            delimiter: Delimiter to use
            
        Returns:
            str: Formatted email string
        """
        return delimiter.join([str(email) for email in emails])
    
    @staticmethod
    def generate_unsubscribe_link(base_url: str, user_id: str, token: str) -> str:
        """Generate unsubscribe link
        
        Args:
            base_url: Base URL of the application
            user_id: User ID
            token: Unsubscribe token
            
        Returns:
            str: Unsubscribe URL
        """
        return f"{base_url.rstrip('/')}/unsubscribe?user_id={user_id}&token={token}"
    
    @staticmethod
    def generate_email_verification_link(base_url: str, user_id: str, token: str) -> str:
        """Generate email verification link
        
        Args:
            base_url: Base URL of the application
            user_id: User ID
            token: Verification token
            
        Returns:
            str: Verification URL
        """
        return f"{base_url.rstrip('/')}/verify-email?user_id={user_id}&token={token}"
    
    @staticmethod
    def generate_password_reset_link(base_url: str, user_id: str, token: str) -> str:
        """Generate password reset link
        
        Args:
            base_url: Base URL of the application
            user_id: User ID
            token: Reset token
            
        Returns:
            str: Password reset URL
        """
        return f"{base_url.rstrip('/')}/reset-password?user_id={user_id}&token={token}"
    
    @staticmethod
    def extract_text_from_html(html_content: str) -> str:
        """Extract plain text from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            str: Plain text content
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except ImportError:
            # Fallback: simple regex-based HTML tag removal
            import re
            clean = re.compile('<.*?>')
            return re.sub(clean, '', html_content)
    
    @staticmethod
    def create_html_email_template(title: str, 
                                 content: str, 
                                 footer: Optional[str] = None,
                                 styles: Optional[str] = None) -> str:
        """Create basic HTML email template
        
        Args:
            title: Email title
            content: Main content
            footer: Optional footer content
            styles: Optional CSS styles
            
        Returns:
            str: HTML email template
        """
        default_styles = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .footer { background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
            .button { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        </style>
        """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            {styles or default_styles}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                {f'<div class="footer">{footer}</div>' if footer else ''}
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    @staticmethod
    def validate_smtp_config(smtp_server: str, 
                           smtp_port: int, 
                           username: str, 
                           password: str,
                           use_tls: bool = True) -> Dict[str, Any]:
        """Validate SMTP configuration
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            use_tls: Whether to use TLS
            
        Returns:
            Dict: Validation result
        """
        result = {
            'valid': False,
            'error': None,
            'server_info': None
        }
        
        try:
            # Create SMTP connection
            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            
            # Login
            server.login(username, password)
            
            # Get server info
            result['server_info'] = {
                'server': smtp_server,
                'port': smtp_port,
                'supports_tls': use_tls
            }
            
            result['valid'] = True
            server.quit()
            
        except smtplib.SMTPAuthenticationError:
            result['error'] = 'Authentication failed'
        except smtplib.SMTPConnectError:
            result['error'] = 'Connection failed'
        except smtplib.SMTPException as e:
            result['error'] = f'SMTP error: {str(e)}'
        except Exception as e:
            result['error'] = f'Unexpected error: {str(e)}'
        
        return result
    
    @staticmethod
    def get_email_provider_settings(email: str) -> Optional[Dict[str, Any]]:
        """Get common SMTP settings for email provider
        
        Args:
            email: Email address
            
        Returns:
            Optional[Dict]: SMTP settings or None if unknown provider
        """
        domain = EmailUtils.extract_domain(email)
        if not domain:
            return None
        
        provider_settings = {
            'gmail.com': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'requires_app_password': True
            },
            'outlook.com': {
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'use_tls': True,
                'requires_app_password': False
            },
            'hotmail.com': {
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'use_tls': True,
                'requires_app_password': False
            },
            'yahoo.com': {
                'smtp_server': 'smtp.mail.yahoo.com',
                'smtp_port': 587,
                'use_tls': True,
                'requires_app_password': True
            }
        }
        
        return provider_settings.get(domain)