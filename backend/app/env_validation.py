"""Startup validation for production configuration (CORS, etc.)."""

import os


def _runtime_env() -> str:
    return (
        (os.getenv("GHOSTWRITER_ENV") or os.getenv("ENVIRONMENT") or "development").strip().lower()
    )


def is_production() -> bool:
    return _runtime_env() == "production"


def validate_production_config() -> None:
    """
    Fail fast in production if CORS is not explicitly configured.

    Wildcard or missing CORS_ORIGINS is unsafe with credentialed requests and
    makes accidental open deployments easier.
    """
    if not is_production():
        return
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        raise RuntimeError(
            "GHOSTWRITER_ENV=production requires CORS_ORIGINS to be set to a comma-separated list "
            "of allowed browser origins (e.g. https://app.example.com). "
            "See README for security notes."
        )
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise RuntimeError(
            "GHOSTWRITER_ENV=production: CORS_ORIGINS is empty after parsing. "
            "Set at least one explicit origin."
        )
    if parts == ["*"]:
        raise RuntimeError(
            "GHOSTWRITER_ENV=production: CORS_ORIGINS must not be '*' only. "
            "Set explicit HTTPS origins for your deployed frontend."
        )

    from app.client_auth import require_email_login

    backend = os.getenv("EMAIL_BACKEND", "smtp").strip().lower()
    if require_email_login() and backend == "resend" and not os.getenv("RESEND_API_KEY", "").strip():
        raise RuntimeError(
            "GHOSTWRITER_ENV=production with email login and EMAIL_BACKEND=resend requires "
            "RESEND_API_KEY to be set (e.g. Railway Variables). Get a key at https://resend.com/api-keys"
        )

    # Default EMAIL_BACKEND is smtp (localhost:1025). If RESEND_API_KEY is set but EMAIL_BACKEND is not resend, sends fail on Railway.
    if os.getenv("RESEND_API_KEY", "").strip() and backend != "resend":
        raise RuntimeError(
            "RESEND_API_KEY is set but EMAIL_BACKEND is not resend (default is smtp). "
            "Set EMAIL_BACKEND=resend on the API service. Otherwise the app tries local SMTP and cannot send mail."
        )
