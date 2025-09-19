"""Email functionality using Gmail SMTP."""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email(to: str, subject: str, html: str) -> bool:
    """
    Send an email using Gmail SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        html: HTML content of the email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get credentials from environment
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        
        if not email_user or not email_pass:
            print("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to
        
        # Add HTML content
        html_part = MIMEText(html, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
        
        print(f"Email sent successfully to {to}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
