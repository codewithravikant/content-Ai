import pytest
from app.postprocess import (
    remove_ai_artifacts,
    parse_content_structure,
    count_words,
    validate_word_count,
    standardize_formatting,
    estimate_read_time,
)
from app.schemas import GenerateRequest, ContentType, Tone


def test_remove_ai_artifacts():
    """Test AI artifact removal."""
    content = "As an AI assistant, I can help you. This is the content."
    cleaned = remove_ai_artifacts(content)
    assert "As an AI assistant" not in cleaned
    assert "This is the content" in cleaned


def test_parse_content_structure_blog():
    """Test blog post structure parsing."""
    content = """# My Blog Post

## Introduction
This is the intro.

## Main Section 1
Content here.

## Conclusion
This is the conclusion.
"""
    parsed = parse_content_structure(content, "blog_post")
    assert parsed["title"] == "My Blog Post"
    assert len(parsed["sections"]) >= 2


def test_parse_content_structure_email():
    """Test email structure parsing."""
    content = """Subject: Follow-up Meeting

Dear John,

This is the email body.

Best regards,
Jane
"""
    parsed = parse_content_structure(content, "email")
    assert "Subject" in str(parsed["sections"])


def test_count_words():
    """Test word counting."""
    text = "This is a test sentence with ten words total for counting."
    assert count_words(text) == 10


def test_validate_word_count():
    """Test word count validation with tolerance."""
    assert validate_word_count(900, 1000, 0.1) == True  # Within ±10%
    assert validate_word_count(1100, 1000, 0.1) == True  # Within ±10%
    assert validate_word_count(850, 1000, 0.1) == False  # Below tolerance
    assert validate_word_count(1150, 1000, 0.1) == False  # Above tolerance


def test_standardize_formatting():
    """Test formatting standardization."""
    content = """# Title

##   Section   


Paragraph with   multiple   spaces.

"""
    formatted = standardize_formatting(content)
    assert "  " not in formatted  # No double spaces
    assert "\n\n\n" not in formatted  # No triple newlines


def test_estimate_read_time():
    """Test reading time estimation."""
    assert estimate_read_time(200) == "1 minute"
    assert estimate_read_time(400) == "2 minutes"
    assert estimate_read_time(1000) == "5 minutes"
