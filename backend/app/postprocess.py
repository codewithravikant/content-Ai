import re
import logging
from typing import Dict, Any, List
from app.schemas import GenerateRequest

logger = logging.getLogger(__name__)


def post_process_content(
    content: str,
    request: GenerateRequest,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Post-process generated content:
    - Parse structure (titles, headers, sections)
    - Validate word count (±10% tolerance)
    - Remove AI artifacts
    - Standardize formatting
    - Detect missing sections
    """
    # Remove AI artifacts
    content = remove_ai_artifacts(content)
    
    # Parse structure
    parsed = parse_content_structure(content, request.content_type.value)
    
    # Validate word count
    word_count = count_words(content)
    target_word_count = request.specifications.get('word_target', 900)
    word_count_valid = validate_word_count(word_count, target_word_count)
    
    if not word_count_valid:
        logger.warning(
            f"Word count validation failed: {word_count} (target: {target_word_count}, "
            f"tolerance: ±10%)"
        )
    
    # Standardize formatting
    content = standardize_formatting(content)
    
    # Validate required sections
    sections_complete = validate_sections(parsed, request.content_type.value)
    
    if not sections_complete:
        logger.warning(f"Missing required sections for {request.content_type.value}")
    
    # Extract metadata
    estimated_read_time = estimate_read_time(word_count)
    seo_keywords = extract_seo_keywords(content) if request.specifications.get('seo_enabled', False) else None
    
    # Extract hashtags for social media content
    hashtags = None
    content_type_val = request.content_type.value
    if content_type_val in ['social_media', 'linkedin']:
        hashtags = extract_hashtags(content)
        if not hashtags or len(hashtags) == 0:
            if content_type_val == 'social_media':
                # If no hashtags found but expected, generate from content
                expected_count = request.specifications.get('hashtag_count', 3)
                hashtags = extract_seo_keywords(content, max_keywords=expected_count)
            elif content_type_val == 'linkedin' and request.specifications.get('include_hashtags', True):
                hashtags = extract_seo_keywords(content, max_keywords=5)
    
    return {
        "content": content,
        "metadata": {
            **metadata,
            "word_count": word_count,
            "sections": parsed.get("sections", []),
            "estimated_read_time": estimated_read_time,
            "seo_keywords": seo_keywords,
            "hashtags": hashtags,
            "word_count_valid": word_count_valid,
            "sections_complete": sections_complete,
        },
    }


def remove_ai_artifacts(content: str) -> str:
    """Remove common AI artifacts from generated content."""
    # Remove phrases like "As an AI assistant", "I'm an AI", etc.
    artifacts = [
        r"as an ai (assistant|model|language model)",
        r"i'm an ai",
        r"i am an ai",
        r"i cannot",
        r"i don't have",
        r"i don't know",
        r"i'm sorry,? but i",
        r"as a (language model|ai)",
    ]
    
    for pattern in artifacts:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)
    
    # Remove incomplete sentences at the end
    content = re.sub(r"[^.!?\n]+$", "", content)
    
    # Clean up extra whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r" {2,}", " ", content)
    
    return content.strip()


def parse_content_structure(content: str, content_type: str) -> Dict[str, List[str]]:
    """Parse content structure (titles, headers, sections)."""
    sections = []
    
    # Extract H1 title
    h1_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    title = h1_match.group(1) if h1_match else None
    
    # Extract H2 sections
    h2_matches = re.finditer(r"^## (.+)$", content, re.MULTILINE)
    for match in h2_matches:
        sections.append(match.group(1))
    
    # For emails, extract subject line
    if content_type == "email":
        subject_match = re.search(r"^Subject:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if subject_match:
            sections.insert(0, f"Subject: {subject_match.group(1)}")
    
    return {
        "title": title,
        "sections": sections,
    }


def count_words(text: str) -> int:
    """Count words in text."""
    # Remove markdown syntax for accurate word count
    text = re.sub(r"[#*`_\[\]()]", "", text)
    words = text.split()
    return len(words)


def validate_word_count(actual: int, target: int, tolerance: float = 0.1) -> bool:
    """
    Validate word count is within ±10% tolerance of target.
    """
    lower_bound = target * (1 - tolerance)
    upper_bound = target * (1 + tolerance)
    return lower_bound <= actual <= upper_bound


def standardize_formatting(content: str) -> str:
    """Standardize markdown formatting and spacing."""
    # Fix unclosed headers (rare but possible)
    content = re.sub(r"^##+[^#\n]*$", lambda m: m.group(0) + "\n", content, flags=re.MULTILINE)
    
    # Standardize spacing around headers
    content = re.sub(r"\n{3,}", "\n\n", content)
    
    # Fix inconsistent capitalization in headers (optional)
    # content = re.sub(r"^## (.+)$", lambda m: f"## {m.group(1).title()}", content, flags=re.MULTILINE)
    
    # Remove trailing whitespace
    content = re.sub(r" +$", "", content, flags=re.MULTILINE)
    
    return content.strip()


def validate_sections(parsed: Dict[str, Any], content_type: str) -> bool:
    """Validate that required sections are present."""
    if content_type == "blog_post":
        # Blog posts should have: title, intro, body sections, conclusion
        sections = parsed.get("sections", [])
        has_title = parsed.get("title") is not None
        has_sections = len(sections) >= 2
        # Check for conclusion keywords
        has_conclusion = any(
            "conclusion" in s.lower() or "summary" in s.lower() or "final" in s.lower()
            for s in sections
        )
        return has_title and has_sections and has_conclusion
    
    elif content_type == "email":
        # Emails should have: subject, greeting, body, closing
        content_lower = parsed.get("sections", [])
        # Basic validation - subject should be present
        return len(content_lower) > 0
    
    elif content_type in ["social_media", "linkedin", "job_application"]:
        # These content types have simpler structure - just need content
        return True
    
    return True


def estimate_read_time(word_count: int) -> str:
    """Estimate reading time in minutes (average 200 words per minute)."""
    minutes = max(1, round(word_count / 200))
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


def extract_seo_keywords(content: str, max_keywords: int = 5) -> List[str]:
    """Extract potential SEO keywords from content headers."""
    # Extract words from headers (H1, H2, H3)
    headers = re.findall(r"^#{1,3} (.+)$", content, re.MULTILINE)
    keywords = []
    
    for header in headers:
        # Extract meaningful words (length > 3, not common stop words)
        words = re.findall(r"\b[a-z]{4,}\b", header.lower())
        keywords.extend(words)
    
    # Remove duplicates and return top keywords
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:max_keywords]


def extract_hashtags(content: str) -> List[str]:
    """Extract hashtags from social media content."""
    # Find all hashtags (format: #word or #word1_word2)
    hashtags = re.findall(r'#(\w+)', content)
    
    # Remove duplicates and clean up
    unique_hashtags = list(dict.fromkeys(hashtags))
    
    # Filter out common/meaningless hashtags
    filtered = [h for h in unique_hashtags if len(h) > 2]
    
    return filtered
