import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings

logger = logging.getLogger("neuroscan.email")


def send_verification_email(to_email: str, code: str) -> None:
    if not settings.SMTP_HOST:
        logger.info(f"[DEV] Verification code for {to_email}: {code}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "NeuroScan - Email Verification"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email

    html = f"""
    <html><body style="font-family:sans-serif;background:#0f1117;color:#e2e8f0;padding:40px">
      <div style="max-width:480px;margin:0 auto;background:#1a1d2e;border-radius:12px;padding:32px">
        <h2 style="color:#6c63ff;margin-top:0">NeuroScan Email Verification</h2>
        <p>Your verification code:</p>
        <div style="font-size:36px;font-weight:700;letter-spacing:8px;color:#fff;
                    background:#0f1117;border-radius:8px;padding:16px 24px;
                    text-align:center;margin:24px 0">{code}</div>
        <p style="color:#94a3b8;font-size:14px">
          This code expires in {settings.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.<br>
          If you did not create a NeuroScan account, ignore this email.
        </p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        logger.info(f"Verification email sent to {to_email}")
