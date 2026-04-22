# backend/app/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings
import os

def send_email(to_email: str, subject: str, content: str):
    message = Mail(
        from_email=os.getenv("EMAIL_FROM"),
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
        return True
    except Exception as e:
        print("Email error:", e)
        return False