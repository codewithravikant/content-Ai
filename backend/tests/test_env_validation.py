import pytest

from app.env_validation import validate_production_config


def test_production_smtp_requires_host_when_email_login_enabled(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", "true")
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_FROM", "Content AI <x@example.com>")

    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        validate_production_config()


def test_production_smtp_rejects_partial_auth(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", "true")
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_FROM", "Content AI <x@example.com>")
    monkeypatch.setenv("SMTP_USER", "x@example.com")
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)

    with pytest.raises(RuntimeError, match="SMTP auth is partially configured"):
        validate_production_config()
