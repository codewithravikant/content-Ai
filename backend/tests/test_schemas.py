import pytest
from app.schemas import (
    GenerateRequest,
    ContentType,
    BlogPostContext,
    EmailContext,
    BlogPostSpecifications,
    EmailSpecifications,
    GenerationParams,
    Tone,
    ExpertiseLevel,
    UrgencyLevel,
)


def test_blog_post_request():
    """Test blog post request validation."""
    request = GenerateRequest(
        content_type=ContentType.BLOG_POST,
        context={
            "topic": "Introduction to Python",
            "audience": "Beginners",
            "tone": Tone.ENGAGING,
        },
        specifications={
            "word_target": 1000,
            "seo_enabled": True,
            "expertise": ExpertiseLevel.BEGINNER,
        },
    )
    assert request.content_type == ContentType.BLOG_POST
    assert request.context["topic"] == "Introduction to Python"


def test_email_request():
    """Test email request validation."""
    request = GenerateRequest(
        content_type=ContentType.EMAIL,
        context={
            "purpose": "Follow-up on meeting",
            "recipient_context": "Client we met last week",
            "key_points": "Thank them, summarize next steps, request feedback",
            "tone": Tone.PROFESSIONAL,
        },
        specifications={
            "urgency_level": UrgencyLevel.MEDIUM,
            "cta": "Please respond by Friday",
        },
    )
    assert request.content_type == ContentType.EMAIL
    assert request.context["purpose"] == "Follow-up on meeting"


def test_generation_params():
    """Test generation parameters validation."""
    params = GenerationParams(
        temperature=0.7,
        max_tokens=2000,
        top_p=0.9,
    )
    assert params.temperature == 0.7
    assert params.max_tokens == 2000
    assert params.top_p == 0.9


def test_invalid_temperature():
    """Test invalid temperature range."""
    with pytest.raises(Exception):
        GenerationParams(temperature=3.0)  # Should be <= 2.0


def test_invalid_word_target():
    """Test invalid word target range."""
    with pytest.raises(Exception):
        BlogPostSpecifications(word_target=50)  # Should be >= 100


def test_empty_context():
    """Test empty context validation."""
    with pytest.raises(Exception):
        GenerateRequest(
            content_type=ContentType.BLOG_POST,
            context={},
            specifications={"word_target": 1000},
        )
