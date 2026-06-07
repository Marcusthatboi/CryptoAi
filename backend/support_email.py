"""Support email delivery helpers for contact requests."""

import os
import smtplib
from email.message import EmailMessage
from typing import Dict


SUPPORT_EMAIL_TO = os.getenv("SUPPORT_EMAIL_TO", "cryptosupport74@gmail.com")
SUPPORT_SMTP_HOST = os.getenv("SUPPORT_SMTP_HOST", "smtp.gmail.com")
SUPPORT_SMTP_PORT = int(os.getenv("SUPPORT_SMTP_PORT", "587"))
SUPPORT_SMTP_USERNAME = os.getenv("SUPPORT_SMTP_USERNAME", "")
SUPPORT_SMTP_PASSWORD = os.getenv("SUPPORT_SMTP_PASSWORD", "")
SUPPORT_SMTP_USE_TLS = os.getenv("SUPPORT_SMTP_USE_TLS", "true").lower() != "false"
SUPPORT_EMAIL_FROM = os.getenv("SUPPORT_EMAIL_FROM", SUPPORT_SMTP_USERNAME or SUPPORT_EMAIL_TO)


def send_email(to_email: str, subject: str, body: str, reply_to: str = "") -> None:
    """Send a generic email using configured SMTP credentials."""
    if not SUPPORT_SMTP_USERNAME or not SUPPORT_SMTP_PASSWORD:
        raise RuntimeError("Support SMTP credentials are not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SUPPORT_EMAIL_FROM
    message["To"] = to_email
    if reply_to:
        message["Reply-To"] = reply_to

    message.set_content(body)

    try:
        with smtplib.SMTP(SUPPORT_SMTP_HOST, SUPPORT_SMTP_PORT, timeout=10) as smtp:
            if SUPPORT_SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(SUPPORT_SMTP_USERNAME, SUPPORT_SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"Failed to send email: {exc}") from exc


def send_support_email(payload: Dict) -> None:
    """Send a support request email using configured SMTP credentials."""
    body_lines = [
        "CryptoAI Support Request",
        "",
        f"Category: {payload.get('category', 'other')}",
        f"Username: {payload.get('username', 'unknown')}",
        f"User ID: {payload.get('user_id', 'unknown')}",
        f"Email: {payload.get('email', 'unknown')}",
        "",
        "Summary:",
        payload.get("summary", "(no summary provided)"),
        "",
        "Details:",
        payload.get("details", "(no details provided)"),
        "",
        "Diagnostics:",
        payload.get("diagnostics", "(no diagnostics provided)")
    ]

    send_email(
        to_email=SUPPORT_EMAIL_TO,
        subject=payload.get("subject", "CryptoAI Support Request"),
        body="\n".join(body_lines),
        reply_to=payload.get("reply_to") or SUPPORT_EMAIL_TO,
    )
