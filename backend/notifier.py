# notifier.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("EMAIL_SMTP_HOST")
SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT") or 0)
SMTP_USER = os.getenv("EMAIL_USERNAME")
SMTP_PASS = os.getenv("EMAIL_PASSWORD")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT") or SMTP_USER

def send_email_alert(subject: str, body_html: str, recipient: str = None):
    recipient = recipient or ALERT_RECIPIENT
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS and recipient):
        print("[notifier] SMTP not configured; skipping email")
        return

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [recipient], msg.as_string())
        server.quit()
        print(f"[notifier] email sent to {recipient}: {subject}")
    except Exception as e:
        print(f"[notifier] failed to send email: {e}")
