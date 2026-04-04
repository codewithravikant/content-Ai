"""Email verification and session tokens."""

import json

import pytest

from app.cache import get_cache
from app.email_auth import hash_verification_code, normalize_email, session_token_valid


@pytest.fixture(autouse=True)
def clear_email_cache():
    """Avoid cross-test leakage for in-memory cache."""
    get_cache().clear()
    yield
    get_cache().clear()


async def test_session_token_invalid_when_empty():
    assert await session_token_valid("") is False


def test_normalize_email():
    assert normalize_email("  User@EXAMPLE.com ") == "user@example.com"


def test_hash_verification_code_stable():
    h1 = hash_verification_code("user@example.com", "123456")
    h2 = hash_verification_code("user@example.com", "123456")
    assert h1 == h2
    assert h1 != hash_verification_code("user@example.com", "000000")


def test_auth_email_config_resend(client, monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "resend")
    r = client.get("/auth/email/config")
    assert r.status_code == 200
    data = r.json()
    assert data["email_backend"] == "resend"
    assert data["dev_inbox_url"] is None


def test_auth_email_config_local_smtp_shows_mailpit_url(client, monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("SMTP_HOST", "localhost")
    r = client.get("/auth/email/config")
    assert r.json()["email_backend"] == "smtp"
    assert r.json()["dev_inbox_url"] == "http://localhost:8025"


def test_auth_email_config_remote_smtp_hides_mailpit_url(client, monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    r = client.get("/auth/email/config")
    assert r.json()["dev_inbox_url"] is None


def test_send_and_verify_flow(client, monkeypatch):
    sent = {}

    async def fake_send(to_email: str, code: str) -> None:
        sent["email"] = to_email
        sent["code"] = code

    monkeypatch.setattr("app.email_service.send_verification_email", fake_send)

    r = client.post("/auth/email/send-code", json={"email": "dev@example.com"})
    assert r.status_code == 200
    assert "code" in sent

    r2 = client.post(
        "/auth/email/verify",
        json={"email": "dev@example.com", "code": sent["code"]},
    )
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    assert token

    r3 = client.get(
        "/auth/email/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200
    assert r3.json()["email"] == "dev@example.com"


def test_generate_accepts_email_session_when_key_configured(
    client, monkeypatch, mock_openai_client
):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")

    captured = {}

    async def capture_send(to_email: str, code: str) -> None:
        captured["c"] = code

    monkeypatch.setattr("app.email_service.send_verification_email", capture_send)
    client.post("/auth/email/send-code", json={"email": "u@example.com"})
    code = captured["c"]

    r = client.post("/auth/email/verify", json={"email": "u@example.com", "code": code})
    token = r.json()["access_token"]

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
    r2 = client.post(
        "/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text


def test_require_email_login_without_api_key(client, monkeypatch, mock_openai_client):
    monkeypatch.delenv("GHOSTWRITER_CLIENT_API_KEY", raising=False)
    monkeypatch.setenv("GHOSTWRITER_REQUIRE_EMAIL_LOGIN", "true")

    r = client.post("/generate", json={})
    assert r.status_code == 401

    captured = {}

    async def capture_send(to_email: str, code: str) -> None:
        captured["c"] = code

    monkeypatch.setattr("app.email_service.send_verification_email", capture_send)
    client.post("/auth/email/send-code", json={"email": "x@example.com"})
    code = captured["c"]
    vr = client.post("/auth/email/verify", json={"email": "x@example.com", "code": code})
    token = vr.json()["access_token"]

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
    ok = client.post(
        "/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 200


async def _fake_stream_chunks(*args, **kwargs):
    yield "chunk"


def test_stream_accepts_session_token_as_api_key_param(client, monkeypatch):
    monkeypatch.setenv("GHOSTWRITER_CLIENT_API_KEY", "secret-key-for-tests")
    monkeypatch.setattr(
        "app.main.ai_client.generate_stream_chunks",
        _fake_stream_chunks,
    )

    captured = {}

    async def capture_send(to_email: str, code: str) -> None:
        captured["c"] = code

    monkeypatch.setattr("app.email_service.send_verification_email", capture_send)
    client.post("/auth/email/send-code", json={"email": "stream@example.com"})
    code = captured["c"]
    vr = client.post("/auth/email/verify", json={"email": "stream@example.com", "code": code})
    token = vr.json()["access_token"]

    data = json.dumps(
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
        params={"data": data, "api_key": token},
        headers={"Accept": "text/event-stream"},
    )
    assert r.status_code == 200
    assert "chunk" in r.text
