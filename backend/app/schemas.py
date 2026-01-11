from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal
from enum import Enum


class ContentType(str, Enum):
    BLOG_POST = "blog_post"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    LINKEDIN = "linkedin"
    JOB_APPLICATION = "job_application"


class Tone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    ENGAGING = "engaging"
    PERSUASIVE = "persuasive"


class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BlogPostContext(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    audience: str = Field(..., min_length=3, max_length=100)
    tone: Tone


class EmailContext(BaseModel):
    purpose: str = Field(..., min_length=5, max_length=200)
    recipient_context: str = Field(..., min_length=5, max_length=500)
    key_points: str = Field(..., min_length=10, max_length=1000)
    tone: Tone


class SocialMediaContext(BaseModel):
    platform: str = Field(..., min_length=2, max_length=50)
    topic: str = Field(..., min_length=3, max_length=500)
    tone: Tone
    goal: Optional[str] = Field(None, max_length=200)


class LinkedInContext(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    target_audience: str = Field(..., min_length=3, max_length=200)
    engagement_goal: Optional[str] = Field(None, max_length=200)
    tone: Tone


class JobApplicationContext(BaseModel):
    position_title: str = Field(..., min_length=3, max_length=200)
    company_name: str = Field(..., min_length=2, max_length=200)
    key_qualifications: str = Field(..., min_length=10, max_length=1000)
    experience_level: str = Field(..., min_length=3, max_length=50)


class BlogPostSpecifications(BaseModel):
    word_target: int = Field(..., ge=50, le=5000)
    seo_enabled: bool = False
    expertise: ExpertiseLevel = ExpertiseLevel.BEGINNER


class EmailSpecifications(BaseModel):
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    cta: Optional[str] = Field(None, max_length=100)


class SocialMediaSpecifications(BaseModel):
    hashtag_count: int = Field(3, ge=0, le=20)
    word_target: int = Field(100, ge=50, le=1000)


class LinkedInSpecifications(BaseModel):
    word_target: int = Field(300, ge=50, le=3000)
    include_hashtags: bool = True


class JobApplicationSpecifications(BaseModel):
    application_type: str = Field("cover_letter", max_length=50)
    word_target: int = Field(400, ge=50, le=1500)


class GenerationParams(BaseModel):
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, ge=100, le=8000)
    top_p: float = Field(0.9, ge=0.0, le=1.0)


class GenerateRequest(BaseModel):
    content_type: ContentType
    context: Dict[str, Any]
    specifications: Dict[str, Any]
    generation_params: Optional[GenerationParams] = None

    @field_validator('context', 'specifications')
    @classmethod
    def validate_dict_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("Context and specifications cannot be empty")
        return v


class ContentMetadata(BaseModel):
    word_count: Optional[int] = None
    sections: Optional[list[str]] = None
    tokens_used: Optional[int] = None
    estimated_read_time: Optional[str] = None
    seo_keywords: Optional[list[str]] = None
    hashtags: Optional[list[str]] = None


class GenerateResponse(BaseModel):
    content: str
    metadata: Optional[ContentMetadata] = None


class ExportPDFRequest(BaseModel):
    content: str
    content_type: ContentType
