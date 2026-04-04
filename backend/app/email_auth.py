"""Email verification codes and opaque session tokens (stored in app cache)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets

from fastapi import HTTPException

from app import email_service
from app.cache import get_cache
from app.rate_limiter import (
    get_email_send_email_limiter,
    get_email_send_ip_limiter,
    get_email_verify_ip_limiter,
)

logger = logging.getLogger(__name__)

CODE_TTL = int(os.getenv("EMAIL_AUTH_CODE_TTL_SECONDS", "600"))
SESSION_TTL = int(os.getenv("EMAIL_AUTH_SESSION_TTL_SECONDS", "604800"))


def _pepper() -> bytes:
    raw = os.getenv("EMAIL_AUTH_CODE_PEPPER", "").strip()
    if raw:
        return raw.encode("utf-8")
    return b"ghostwriter-dev-email-pepper-change-me"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_verification_code(email: str, code: str) -> str:
    ne = normalize_email(email)
    return hmac.new(_pepper(), f"{ne}:{code.strip()}".encode("utf-8"), hashlib.sha256).hexdigest()


async def session_token_valid(token: str) -> bool:
    if not token or not token.strip():
        return False
    cache = get_cache()
    val = await cache.get(f"email_session:{token.strip()}")
    return val is not None


async def session_email_for_token(token: str) -> str | None:
    if not token or not token.strip():
        return None
    cache = get_cache()
    val = await cache.get(f"email_session:{token.strip()}")
    return val if isinstance(val, str) else None


async def revoke_session_token(token: str) -> None:
    if not token or not token.strip():
        return
    cache = get_cache()
    await cache.delete(f"email_session:{token.strip()}")


async def request_verification_code(email: str, client_ip: str) -> None:
    ne = normalize_email(email)
    if not await get_email_send_ip_limiter().is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests from this network. Try again later.",
        )
    if not await get_email_send_email_limiter().is_allowed(ne):
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests for this email. Try again later.",
        )

    code = f"{secrets.randbelow(10**6):06d}"
    code_hash = hash_verification_code(ne, code)
    cache = get_cache()
    await cache.set(f"email_vercode:{ne}", {"h": code_hash}, ttl=CODE_TTL)

    try:
        await email_service.send_verification_email(ne, code)
    except Exception:
        logger.exception("Failed to send verification email to %s", ne)
        await cache.delete(f"email_vercode:{ne}")
        raise HTTPException(
            status_code=503,
            detail=(
                "We could not send the verification email. "
                "For local SMTP: run `make mailpit` in a second terminal (Mailpit on localhost:1025), "
                "then retry. Or set EMAIL_BACKEND=resend with RESEND_API_KEY in backend/.env. "
                "See `make email-help`."
            ),
        )


async def verify_code_and_issue_session(email: str, code: str, client_ip: str) -> str:
    if not await get_email_verify_ip_limiter().is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts. Try again later.",
        )

    ne = normalize_email(email)
    cache = get_cache()
    entry = await cache.get(f"email_vercode:{ne}")
    if not entry or not isinstance(entry, dict) or "h" not in entry:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    expected = entry["h"]
    candidate = hash_verification_code(ne, code)
    if not secrets.compare_digest(expected, candidate):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    await cache.delete(f"email_vercode:{ne}")
    token = secrets.token_urlsafe(32)
    await cache.set(f"email_session:{token}", ne, ttl=SESSION_TTL)
    return token
