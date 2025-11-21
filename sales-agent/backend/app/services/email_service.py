import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from ..config import settings

class EmailService:
    """Email service supporting both MailHog (testing) and real SMTP (Gmail, etc.)"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.from_email = settings.EMAIL_FROM
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_pass = getattr(settings, 'SMTP_PASS', None)
        
        # Auto-detect if we're using a real SMTP server (requires auth)
        self.use_auth = bool(self.smtp_user and self.smtp_pass)
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str
    ) -> bool:
        """
        Send email via SMTP
        
        Supports:
        - MailHog (no auth, port 1025) - for testing
        - Gmail (TLS auth, port 587) - for production
        - Any SMTP server
        
        Returns True if successful
        """
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            if self.use_auth:
                # Production mode: Use TLS authentication (Gmail, SendGrid, etc.)
                print(f"📧 Sending email via {self.smtp_host} (authenticated)")
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()  # Upgrade to secure connection
                    server.ehlo()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.sendmail(self.from_email, [to_email], msg.as_string())
            else:
                # Testing mode: MailHog (no auth)
                print(f"📧 Sending email via {self.smtp_host} (no auth - MailHog)")
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.sendmail(self.from_email, [to_email], msg.as_string())
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {str(e)}")
            print("💡 Tip: For Gmail, use an App Password, not your regular password")
            return False
        except Exception as e:
            print(f"❌ Email send failed: {str(e)}")
            return False
