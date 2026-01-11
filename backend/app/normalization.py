from app.schemas import (
    GenerateRequest,
    ContentType,
    BlogPostContext,
    EmailContext,
    SocialMediaContext,
    LinkedInContext,
    JobApplicationContext,
    BlogPostSpecifications,
    EmailSpecifications,
    SocialMediaSpecifications,
    LinkedInSpecifications,
    JobApplicationSpecifications,
    GenerationParams,
    Tone,
    ExpertiseLevel,
    UrgencyLevel,
)
from typing import Dict, Any


def validate_request(request: GenerateRequest) -> GenerateRequest:
    """
    Validate the incoming request structure.
    """
    valid_types = [
        ContentType.BLOG_POST,
        ContentType.EMAIL,
        ContentType.SOCIAL_MEDIA,
        ContentType.LINKEDIN,
        ContentType.JOB_APPLICATION,
    ]
    if request.content_type not in valid_types:
        raise ValueError(f"Unsupported content type: {request.content_type}")
    
    # Validate context structure based on content type
    if request.content_type == ContentType.BLOG_POST:
        try:
            BlogPostContext(**request.context)
        except Exception as e:
            raise ValueError(f"Invalid blog post context: {e}")
    elif request.content_type == ContentType.EMAIL:
        try:
            EmailContext(**request.context)
        except Exception as e:
            raise ValueError(f"Invalid email context: {e}")
    elif request.content_type == ContentType.SOCIAL_MEDIA:
        try:
            SocialMediaContext(**request.context)
        except Exception as e:
            raise ValueError(f"Invalid social media context: {e}")
    elif request.content_type == ContentType.LINKEDIN:
        try:
            LinkedInContext(**request.context)
        except Exception as e:
            raise ValueError(f"Invalid linkedin context: {e}")
    elif request.content_type == ContentType.JOB_APPLICATION:
        try:
            JobApplicationContext(**request.context)
        except Exception as e:
            raise ValueError(f"Invalid job application context: {e}")
    
    # Validate specifications structure
    if request.content_type == ContentType.BLOG_POST:
        try:
            BlogPostSpecifications(**request.specifications)
        except Exception as e:
            raise ValueError(f"Invalid blog post specifications: {e}")
    elif request.content_type == ContentType.EMAIL:
        try:
            EmailSpecifications(**request.specifications)
        except Exception as e:
            raise ValueError(f"Invalid email specifications: {e}")
    elif request.content_type == ContentType.SOCIAL_MEDIA:
        try:
            SocialMediaSpecifications(**request.specifications)
        except Exception as e:
            raise ValueError(f"Invalid social media specifications: {e}")
    elif request.content_type == ContentType.LINKEDIN:
        try:
            LinkedInSpecifications(**request.specifications)
        except Exception as e:
            raise ValueError(f"Invalid linkedin specifications: {e}")
    elif request.content_type == ContentType.JOB_APPLICATION:
        try:
            JobApplicationSpecifications(**request.specifications)
        except Exception as e:
            raise ValueError(f"Invalid job application specifications: {e}")
    
    return request


def normalize_request(request: GenerateRequest) -> GenerateRequest:
    """
    Normalize the request by converting raw values to standardized formats.
    - Normalize tone to lowercase
    - Set default generation parameters based on content type
    - Ensure consistent structure
    """
    # Normalize context
    normalized_context = {}
    for key, value in request.context.items():
        if isinstance(value, str):
            normalized_context[key] = value.strip()
            # Normalize tone
            if key == "tone":
                normalized_context[key] = normalize_tone(value)
        else:
            normalized_context[key] = value
    
    # Normalize specifications
    normalized_specs = {}
    for key, value in request.specifications.items():
        if key == "word_target" and isinstance(value, str):
            # Handle word count ranges like "800-1000"
            normalized_specs[key] = normalize_word_count(value)
        elif isinstance(value, str):
            normalized_specs[key] = value.strip().lower()
        else:
            normalized_specs[key] = value
    
    # Set default generation parameters if not provided
    if not request.generation_params:
        normalized_params = get_default_generation_params(request.content_type)
    else:
        normalized_params = request.generation_params
    
    return GenerateRequest(
        content_type=request.content_type,
        context=normalized_context,
        specifications=normalized_specs,
        generation_params=normalized_params,
    )


def normalize_word_count(word_count: str) -> int:
    """
    Convert word count range (e.g., "800-1000") to target integer (median).
    Minimum is 50 words.
    """
    if isinstance(word_count, int):
        return max(50, word_count)
    
    parts = word_count.split("-")
    if len(parts) == 2:
        try:
            min_val = int(parts[0].strip())
            max_val = int(parts[1].strip())
            if min_val > 0 and max_val > 0 and min_val <= max_val:
                result = (min_val + max_val) // 2
                return max(50, result)  # Ensure minimum 50
        except ValueError:
            pass
    
    # Default fallback (minimum 50)
    return max(50, 900)


def normalize_tone(tone: str) -> str:
    """
    Normalize tone string to lowercase and validate.
    """
    normalized = tone.strip().lower()
    try:
        Tone(normalized)
        return normalized
    except ValueError:
        # Return default if invalid
        return Tone.ENGAGING.value


def get_default_generation_params(content_type: ContentType) -> GenerationParams:
    """
    Get default AI generation parameters based on content type.
    """
    if content_type == ContentType.BLOG_POST:
        return GenerationParams(
            temperature=0.7,  # Balanced creativity
            max_tokens=2000,
            top_p=0.9,
        )
    elif content_type == ContentType.EMAIL:
        return GenerationParams(
            temperature=0.6,  # More focused for emails
            max_tokens=1500,
            top_p=0.85,
        )
    elif content_type == ContentType.SOCIAL_MEDIA:
        return GenerationParams(
            temperature=0.8,  # More creative for social media
            max_tokens=500,
            top_p=0.95,
        )
    elif content_type == ContentType.LINKEDIN:
        return GenerationParams(
            temperature=0.65,  # Professional but engaging
            max_tokens=800,
            top_p=0.9,
        )
    elif content_type == ContentType.JOB_APPLICATION:
        return GenerationParams(
            temperature=0.55,  # Professional and focused
            max_tokens=1200,
            top_p=0.85,
        )
    else:
        return GenerationParams()  # Use schema defaults
