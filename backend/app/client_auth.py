"""
Optional shared-secret authentication for API clients.

When GHOSTWRITER_CLIENT_API_KEY is set, expensive routes require the same value via
Authorization: Bearer, X-API-Key, or (for SSE only) the api_key query parameter.

Never log the client key or place it in error messages.
"""

from __future__ import annotations

import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.email_auth import session_token_valid
from app.env_validation import is_production


def client_api_key_expected() -> str | None:
    """Return configured key, or None if client auth is disabled."""
    raw = os.getenv("GHOSTWRITER_CLIENT_API_KEY", "")
    if not raw or not raw.strip():
        return None
    return raw.strip()


def extract_client_token(request: Request) -> str | None:
    """Bearer, X-API-Key, or api_key query param (for /generate/stream only)."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    x = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if x:
        return x.strip()
    path = request.scope.get("path", "")
    if path == "/generate/stream":
        q = request.query_params.get("api_key")
        if q:
            return q.strip()
    return None


def require_email_login() -> bool:
    """When true, protected routes require a valid email session token unless the API key matches."""
    v = os.getenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    if not v:
        return is_production()
    return False


def paths_requiring_client_key(method: str, path: str) -> bool:
    # CORS preflight must not require a client key or browsers cannot call the API.
    if method == "OPTIONS":
        return False
    if method == "POST" and path == "/generate":
        return True
    if method == "GET" and path == "/generate/stream":
        return True
    if method == "POST" and path == "/export/pdf":
        return True
    if method == "GET" and path == "/metrics":
        return True
    return False


class ClientAuthMiddleware(BaseHTTPMiddleware):
    """
    Enforces GHOSTWRITER_CLIENT_API_KEY when set.

    Registered so it runs after StripApiPrefixMiddleware: paths are already /generate, etc.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        method = request.method
        if not paths_requiring_client_key(method, path):
            return await call_next(request)

        expected = client_api_key_expected()
        need_login = require_email_login()
        if not expected and not need_login:
            return await call_next(request)

        token = extract_client_token(request)
        ok_key = bool(expected and token and secrets.compare_digest(token, expected))
        ok_session = bool(token and await session_token_valid(token))

        if ok_key or ok_session:
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={
                "detail": (
                    "Authentication required. Provide a valid client API key "
                    "(Authorization: Bearer or X-API-Key) or sign in with email."
                ),
            },
        )
