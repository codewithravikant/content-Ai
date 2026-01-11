import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


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
