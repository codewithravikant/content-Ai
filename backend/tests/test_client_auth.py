"""Client API key middleware and production CORS validation."""

import pytest

from app.client_auth import require_email_login
from app.env_validation import validate_production_config


def test_validate_production_requires_cors_origins(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_production_config()


def test_validate_production_rejects_wildcard_only(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="must not be"):
        validate_production_config()


def test_validate_production_accepts_explicit_origins(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://www.example.com")
    validate_production_config()


def test_require_email_login_unset_false_in_development(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "development")
    monkeypatch.delenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", raising=False)
    assert require_email_login() is False


def test_require_email_login_unset_true_in_production(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.delenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", raising=False)
    assert require_email_login() is True


def test_require_email_login_explicit_false_in_production(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", "false")
    assert require_email_login() is False


def test_validate_production_resend_requires_api_key(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("EMAIL_BACKEND", "resend")
    monkeypatch.delenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        validate_production_config()


def test_validate_production_resend_ok_with_api_key(monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("EMAIL_BACKEND", "resend")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.delenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", raising=False)
    validate_production_config()


def test_health_unauthenticated_with_client_key(client, monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    r = client.get("/health")
    assert r.status_code == 200


def test_generate_requires_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    r = client.post("/generate", json={})
    assert r.status_code == 401
    assert "Authentication" in r.json().get("detail", "")


def test_generate_accepts_bearer_key(client, monkeypatch, mock_openai_client):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    payload = {
        "content_type": "blog_post",
        "context": {
            "topic": "Introduction to Python",
            "audience": "Beginners",
            "tone": "engaging",
        },
        "specifications": {
            "word_target": 500,
            "seo_enabled": True,
            "expertise": "beginner",
        },
    }
    r = client.post(
        "/generate",
        json=payload,
        headers={"Authorization": "Bearer secret-key-for-tests"},
    )
    assert r.status_code == 200, r.text


async def _fake_stream_chunks(*args, **kwargs):
    yield "chunk"


def test_stream_accepts_query_key(client, monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    monkeypatch.setattr(
        "app.main.ai_client.generate_stream_chunks",
        _fake_stream_chunks,
    )
    import json as json_lib

    data = json_lib.dumps(
        {
            "content_type": "blog_post",
            "context": {
                "topic": "Introduction to Python",
                "audience": "Beginners",
                "tone": "engaging",
            },
            "specifications": {
                "word_target": 500,
                "seo_enabled": True,
                "expertise": "beginner",
            },
        }
    )
    r = client.get(
        "/generate/stream",
        params={"data": data, "api_key": "secret-key-for-tests"},
        headers={"Accept": "text/event-stream"},
    )
    assert r.status_code == 200
    assert "chunk" in r.text


def test_metrics_requires_key_when_configured(client, monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    assert client.get("/metrics").status_code == 401
    assert (
        client.get(
            "/metrics",
            headers={"X-API-Key": "secret-key-for-tests"},
        ).status_code
        == 200
    )
