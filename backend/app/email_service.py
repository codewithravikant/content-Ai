"""
Send verification email via SMTP (Mailpit/MailHog in dev) or Resend HTTP API.

Set EMAIL_BACKEND=smtp (default) or EMAIL_BACKEND=resend.
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

import httpx

logger = logging.getLogger(__name__)


async def send_verification_email(to_email: str, code: str) -> None:
    subject = "Your Ghostwriter verification code"
    body_text = (
        f"Your verification code is: {code}\n\n"
        "This code expires in 10 minutes. If you did not request this, you can ignore this message."
    )
    backend = os.getenv("EMAIL_BACKEND", "smtp").strip().lower()
    if backend == "resend":
        await _send_resend(to_email, subject, body_text)
    else:
        await asyncio.to_thread(_send_smtp_sync, to_email, subject, body_text)


def _send_smtp_sync(to_email: str, subject: str, body_text: str) -> None:
    host = os.getenv("SMTP_HOST", "localhost").strip()
    port = int(os.getenv("SMTP_PORT", "1025"))
    from_addr = os.getenv("SMTP_FROM", "ghostwriter@localhost").strip()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body_text)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if os.getenv("SMTP_USE_TLS", "").strip().lower() in ("1", "true", "yes", "on"):
            smtp.starttls()
        user = os.getenv("SMTP_USER", "").strip()
        pw = os.getenv("SMTP_PASSWORD", "").strip()
        if user:
            smtp.login(user, pw)
        smtp.send_message(msg)


async def _send_resend(to_email: str, subject: str, body_text: str) -> None:
    key = os.getenv("RESEND_API_KEY", "").strip()
    if not key:
        raise RuntimeError("RESEND_API_KEY is required when EMAIL_BACKEND=resend")
    from_addr = os.getenv("RESEND_FROM", "onboarding@resend.dev").strip()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "text": body_text,
            },
        )
        if r.status_code >= 400:
            logger.error("Resend API error: %s %s", r.status_code, r.text[:500])
        r.raise_for_status()
