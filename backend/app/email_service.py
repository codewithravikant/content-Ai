"""
Send verification email via SMTP (Mailpit/MailHog in dev, or e.g. Gmail) or Resend HTTP API.

Set EMAIL_BACKEND=smtp (default) or EMAIL_BACKEND=resend.

Gmail: use smtp.gmail.com, port 465 (SSL) or 587 (STARTTLS), and an App Password (not your normal password).
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

import httpx

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Email could not be sent; message is intended for API clients (no secrets)."""


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
        try:
            await asyncio.to_thread(_send_smtp_sync, to_email, subject, body_text)
        except EmailSendError:
            raise
        except smtplib.SMTPException as exc:
            logger.exception("SMTP send failed")
            raise EmailSendError(
                "Could not send email via SMTP. Check SMTP_HOST, port, SMTP_USER, and password "
                "(Gmail requires an app password and often port 465 with SSL or 587 with STARTTLS)."
            ) from exc
        except OSError as exc:
            logger.exception("SMTP connection failed")
            raise EmailSendError(
                f"Could not connect to the SMTP server ({os.getenv('SMTP_HOST', 'localhost')}). "
                "Check SMTP_HOST and SMTP_PORT."
            ) from exc


def _smtp_from_header() -> str:
    """SMTP_FROM or EMAIL_FROM; supports `Name <email@domain.com>`, plain email, or `Name email@domain`."""
    raw = (os.getenv("SMTP_FROM") or os.getenv("EMAIL_FROM") or "ghostwriter@localhost").strip()
    if not raw:
        return "ghostwriter@localhost"
    name, addr = parseaddr(raw)
    if addr:
        if name:
            return formataddr((name, addr))
        return addr
    m = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", raw)
    if m:
        email_addr = m.group(1)
        display = raw[: raw.find(email_addr)].strip()
        if display:
            return formataddr((display, email_addr))
        return email_addr
    return raw


def _smtp_password() -> str:
    raw = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or "").strip()
    if not raw:
        return ""
    # Gmail app passwords are often pasted with spaces between groups
    return re.sub(r"\s+", "", raw)


def _send_smtp_sync(to_email: str, subject: str, body_text: str) -> None:
    host = os.getenv("SMTP_HOST", "localhost").strip()
    port = int(os.getenv("SMTP_PORT", "1025"))
    from_header = _smtp_from_header()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to_email
    msg.set_content(body_text)

    tls_env = os.getenv("SMTP_USE_TLS", "").strip().lower() in ("1", "true", "yes", "on")
    ssl_env = os.getenv("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes", "on")
    use_ssl = ssl_env or port == 465
    use_starttls = (tls_env or port == 587) and not use_ssl

    user = os.getenv("SMTP_USER", "").strip()
    pw = _smtp_password()

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            if user:
                smtp.login(user, pw)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_starttls:
            smtp.starttls()
        if user:
            smtp.login(user, pw)
        smtp.send_message(msg)


async def _send_resend(to_email: str, subject: str, body_text: str) -> None:
    key = os.getenv("RESEND_API_KEY", "").strip()
    if not key:
        raise EmailSendError(
            "Resend is selected but RESEND_API_KEY is not set. Add it to the server environment (e.g. Railway Variables)."
        )
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
        # 401 = bad API key. 403 is also used for validation (e.g. testing mode: only your account email).
        if r.status_code == 401:
            logger.error("Resend API auth error: %s %s", r.status_code, r.text[:500])
            raise EmailSendError(
                "Resend rejected the API key. Create a new key at resend.com/api-keys and update RESEND_API_KEY."
            )
        if 400 <= r.status_code < 500:
            logger.error("Resend API error: %s %s", r.status_code, r.text[:500])
            detail = "Resend could not send this message."
            try:
                data = r.json()
                if isinstance(data, dict) and isinstance(data.get("message"), str):
                    detail = f"Resend: {data['message']}"
            except Exception:
                pass
            raise EmailSendError(detail)
        if r.status_code >= 500:
            logger.error("Resend API error: %s %s", r.status_code, r.text[:500])
            detail = "Resend had a temporary error. Try again in a minute."
            try:
                data = r.json()
                if isinstance(data, dict) and isinstance(data.get("message"), str):
                    detail = f"Resend: {data['message']}"
            except Exception:
                pass
            raise EmailSendError(detail)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Resend unexpected status: %s", exc)
            raise EmailSendError(
                "Resend returned an unexpected response. Check API logs and resend.com status."
            ) from exc
