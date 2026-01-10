"""
Email Service module for sending notifications via SMTP.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from typing import Dict, Optional, Tuple

from backend.core.db_pool import get_connection

class EmailService:
    @staticmethod
    def get_smtp_config() -> Optional[Dict]:
        """Fetch SMTP configuration from database."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT host, port, username, password, from_email, use_tls FROM smtp_config WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return {
                    "host": row[0],
                    "port": row[1],
                    "username": row[2],
                    "password": row[3],
                    "from_email": row[4],
                    "use_tls": bool(row[5])
                }
            return None
        except Exception as e:
            print(f"[EmailService] Failed to load config: {e}")
            return None

    @staticmethod
    def save_smtp_config(config: Dict) -> None:
        """Save or update SMTP configuration."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO smtp_config (id, host, port, username, password, from_email, use_tls)
                VALUES (1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    host = excluded.host,
                    port = excluded.port,
                    username = excluded.username,
                    password = excluded.password,
                    from_email = excluded.from_email,
                    use_tls = excluded.use_tls
            """, (
                config["host"],
                config["port"],
                config["username"],
                config["password"],
                config.get("from_email", config["username"]), # Default from_email to username
                1 if config.get("use_tls", True) else 0
            ))
            conn.commit()
        except Exception as e:
            print(f"[EmailService] Failed to save config: {e}")
            raise

    @staticmethod
    def send_email(to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send an email using stored connection details."""
        config = EmailService.get_smtp_config()
        if not config:
            print("[EmailService] No SMTP configuration found.")
            return False

        msg = MIMEMultipart()
        msg['From'] = config['from_email'] or config['username']
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        try:
            # Connect to valid SMTP server
            server = smtplib.SMTP(config['host'], config['port'])
            
            if config['use_tls']:
                server.starttls()
            
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            print(f"[EmailService] Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"[EmailService] Failed to send email: {e}")
            return False

    @staticmethod
    def send_welcome_email(username: str, email: str) -> bool:
        """Send welcome email to new user."""
        subject = "Welcome to Agentry!"
        body = f"""
        <html>
        <body>
            <h2>Welcome to Agentry, {username}!</h2>
            <p>You have successfully registered into Agentry. We're excited to have you on board!</p>
            <br>
            <p>Best regards,<br>The Agentry Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(email, subject, body, is_html=True)

    @staticmethod
    def send_password_reset_email(email: str, token: str) -> bool:
        """Send password reset token."""
        subject = "Reset your Agentry Password"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password.</p>
            <p>Your password reset code is: <strong>{token}</strong></p>
            <p>Please enter this code in the application to initiate the reset.</p>
            <br>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The Agentry Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(email, subject, body, is_html=True)

    @staticmethod
    def send_password_changed_email(username: str, email: str) -> bool:
        """Send password changed confirmation."""
        subject = "Your Agentry Password has been changed"
        body = f"""
        <html>
        <body>
            <h2>Password Changed</h2>
            <p>Hello {username},</p>
            <p>Your password has been successfully reset. You can now login with your new password.</p>
            <br>
            <p>Best regards,<br>The Agentry Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(email, subject, body, is_html=True)
