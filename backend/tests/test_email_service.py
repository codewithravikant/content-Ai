import pytest

from app import email_service


def test_smtp_password_normalizes_whitespace(monkeypatch):
    monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")
    assert email_service._smtp_password() == "abcdefghijklmnop"


@pytest.mark.asyncio
async def test_send_verification_email_uses_smtp_backend(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    calls = {"smtp": 0}

    def fake_smtp(*args, **kwargs):
        calls["smtp"] += 1

    monkeypatch.setattr("app.email_service._send_smtp_sync", fake_smtp)

    await email_service.send_verification_email("u@example.com", "123456")
    assert calls["smtp"] == 1


def test_smtp_gmail_fallback_attempt_order_from_465(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "1")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")

    attempted_ports = []

    class FakeSMTPSSL:
        def __init__(self, host, port, timeout):
            attempted_ports.append(port)
            raise OSError("blocked")

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            attempted_ports.append(port)
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def send_message(self, msg):
            return None

    monkeypatch.setattr("app.email_service.smtplib.SMTP_SSL", FakeSMTPSSL)
    monkeypatch.setattr("app.email_service.smtplib.SMTP", FakeSMTP)
    email_service._send_smtp_sync("u@example.com", "s", "b")
    assert attempted_ports == [465, 587]
