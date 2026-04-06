import pytest

from app import email_service


def test_smtp_password_normalizes_whitespace(monkeypatch):
    monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")
    assert email_service._smtp_password() == "abcdefghijklmnop"


@pytest.mark.asyncio
async def test_send_verification_email_uses_resend_backend(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "resend")
    calls = {"resend": 0, "smtp": 0}

    async def fake_resend(*args, **kwargs):
        calls["resend"] += 1

    def fake_smtp(*args, **kwargs):
        calls["smtp"] += 1

    monkeypatch.setattr("app.email_service._send_resend", fake_resend)
    monkeypatch.setattr("app.email_service._send_smtp_sync", fake_smtp)

    await email_service.send_verification_email("u@example.com", "123456")
    assert calls["resend"] == 1
    assert calls["smtp"] == 0


@pytest.mark.asyncio
async def test_send_verification_email_uses_smtp_backend(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    calls = {"resend": 0, "smtp": 0}

    async def fake_resend(*args, **kwargs):
        calls["resend"] += 1

    def fake_smtp(*args, **kwargs):
        calls["smtp"] += 1

    monkeypatch.setattr("app.email_service._send_resend", fake_resend)
    monkeypatch.setattr("app.email_service._send_smtp_sync", fake_smtp)

    await email_service.send_verification_email("u@example.com", "123456")
    assert calls["smtp"] == 1
    assert calls["resend"] == 0
