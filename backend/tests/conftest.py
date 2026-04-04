import os

# Ensure production startup validation does not run during tests unless overridden.
os.environ.setdefault("GHOSTWRITER_ENV", "development")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """Create test client (runs app lifespan startup, including env validation)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI client for testing."""

    async def mock_generate_stream(*args, **kwargs):
        return {
            "content": "# Test Blog Post\n\n## Introduction\n\nThis is a test blog post.",
            "metadata": {
                "tokens_used": 100,
                "model": "gpt-3.5-turbo",
            },
        }

    monkeypatch.setattr("app.ai_client.AIClient.generate_stream", mock_generate_stream)
