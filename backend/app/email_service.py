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

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Email could not be sent; message is intended for API clients (no secrets)."""


async def send_verification_email(to_email: str, code: str) -> None:
    subject = "Your Ghostwriter verification code"
    body_text = (
        f"Your verification code is: {code}\n\n"
        "This code expires in 10 minutes. If you did not request this, you can ignore this message."
    )
    try:
        await asyncio.to_thread(_send_smtp_sync, to_email, subject, body_text)
    except EmailSendError:
        raise
    except smtplib.SMTPException as exc:
        logger.exception("SMTP send failed")
        raise EmailSendError(
            "Could not send email via SMTP. Check SMTP_HOST, port, SMTP_USER, and app password "
            "(Gmail requires an app password and usually works on 465 SSL or 587 STARTTLS)."
        ) from exc
    except OSError as exc:
        logger.exception("SMTP connection failed")
        raise EmailSendError(
            f"Could not connect to the SMTP server ({os.getenv('SMTP_HOST', 'localhost')}). "
            f"Check SMTP_HOST/SMTP_PORT and network egress. System error: {exc}"
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
    configured_port = int(os.getenv("SMTP_PORT", "1025"))
    from_header = _smtp_from_header()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to_email
    msg.set_content(body_text)

    tls_env = os.getenv("SMTP_USE_TLS", "").strip().lower() in ("1", "true", "yes", "on")
    ssl_env = os.getenv("SMTP_USE_SSL", "").strip().lower() in ("1", "true", "yes", "on")
    user = os.getenv("SMTP_USER", "").strip()
    pw = _smtp_password()

    # Gmail-only friendly fallback: if one port is blocked by network policy, try the other standard port.
    attempts: list[tuple[int, bool, bool]] = []
    use_ssl = ssl_env or configured_port == 465
    use_starttls = (tls_env or configured_port == 587) and not use_ssl
    attempts.append((configured_port, use_ssl, use_starttls))
    if host == "smtp.gmail.com":
        if configured_port == 465:
            attempts.append((587, False, True))
        elif configured_port == 587:
            attempts.append((465, True, False))

    last_exc: Exception | None = None
    for port, attempt_ssl, attempt_starttls in attempts:
        try:
            if attempt_ssl:
                with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                    if user:
                        smtp.login(user, pw)
                    smtp.send_message(msg)
                return
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                if attempt_starttls:
                    smtp.starttls()
                if user:
                    smtp.login(user, pw)
                smtp.send_message(msg)
            return
        except (OSError, smtplib.SMTPException) as exc:
            last_exc = exc
            logger.warning("SMTP attempt failed host=%s port=%s ssl=%s: %s", host, port, attempt_ssl, exc)

    if last_exc:
        raise last_exc
