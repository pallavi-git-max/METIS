#!/usr/bin/env python3
"""Test SMTP configuration and email sending"""

from app import app
from backend.services.email_service import EmailService

def test_smtp_config():
    with app.app_context():
        print("=== SMTP Configuration Test ===")
        print(f"SMTP_SERVER: {app.config.get('SMTP_SERVER')}")
        print(f"SMTP_PORT: {app.config.get('SMTP_PORT')}")
        print(f"SMTP_USERNAME: {app.config.get('SMTP_USERNAME')}")
        print(f"SMTP_PASSWORD: {'***' if app.config.get('SMTP_PASSWORD') else 'NOT SET'}")
        print(f"FROM_EMAIL: {app.config.get('FROM_EMAIL')}")
        print(f"FROM_NAME: {app.config.get('FROM_NAME')}")
        
        # Test email service
        email_service = EmailService()
        print(f"\nEmailService SMTP_USERNAME: {email_service.smtp_username}")
        print(f"EmailService SMTP_PASSWORD: {'***' if email_service.smtp_password else 'NOT SET'}")
        
        # Test sending email
        print("\n=== Testing Email Send ===")
        test_email = "maths.hub143@gmail.com"  # Change this to your real email for testing
        success = email_service.send_email(
            to_email=test_email,
            subject="SMTP Test",
            html_content="<h1>SMTP Test</h1><p>If you receive this, SMTP is working!</p>",
            text_content="SMTP Test - If you receive this, SMTP is working!"
        )
        print(f"Email send result: {success}")

if __name__ == "__main__":
    test_smtp_config()
