import pytest
from app.normalization import (
    normalize_word_count,
    normalize_tone,
    get_default_generation_params,
    normalize_request,
    validate_request,
)
from app.schemas import GenerateRequest, ContentType, Tone, ExpertiseLevel


def test_normalize_word_count():
    """Test word count normalization."""
    assert normalize_word_count("800-1000") == 900
    assert normalize_word_count("500-700") == 600
    assert normalize_word_count("1000") == 900  # Fallback for invalid format


def test_normalize_tone():
    """Test tone normalization."""
    assert normalize_tone("PROFESSIONAL") == "professional"
    assert normalize_tone("  Engaging  ") == "engaging"
    assert normalize_tone("invalid") == "engaging"  # Default fallback


def test_get_default_generation_params():
    """Test default generation parameters."""
    blog_params = get_default_generation_params(ContentType.BLOG_POST)
    assert blog_params.temperature == 0.7
    assert blog_params.max_tokens == 2000
    
    email_params = get_default_generation_params(ContentType.EMAIL)
    assert email_params.temperature == 0.6
    assert email_params.max_tokens == 1500


def test_normalize_request():
    """Test request normalization."""
    request = GenerateRequest(
        content_type=ContentType.BLOG_POST,
        context={
            "topic": "  Test Topic  ",
            "audience": "General Public",
            "tone": Tone.ENGAGING,
        },
        specifications={
            "word_target": "800-1000",
            "seo_enabled": True,
            "expertise": ExpertiseLevel.BEGINNER,
        },
    )
    
    normalized = normalize_request(request)
    assert normalized.context["topic"] == "Test Topic"  # Trimmed
    assert normalized.specifications["word_target"] == 900  # Normalized


def test_validate_request():
    """Test request validation."""
    request = GenerateRequest(
        content_type=ContentType.BLOG_POST,
        context={
            "topic": "Test Topic",
            "audience": "General Public",
            "tone": Tone.ENGAGING,
        },
        specifications={
            "word_target": 1000,
            "seo_enabled": True,
            "expertise": ExpertiseLevel.BEGINNER,
        },
    )
    
    validated = validate_request(request)
    assert validated.content_type == ContentType.BLOG_POST


def test_validate_invalid_request():
    """Test invalid request validation."""
    request = GenerateRequest(
        content_type=ContentType.BLOG_POST,
        context={
            "topic": "T",  # Too short
            "audience": "General Public",
            "tone": Tone.ENGAGING,
        },
        specifications={
            "word_target": 1000,
            "seo_enabled": True,
            "expertise": ExpertiseLevel.BEGINNER,
        },
    )
    
    with pytest.raises(ValueError):
        validate_request(request)
