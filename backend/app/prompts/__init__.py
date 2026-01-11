from app.schemas import GenerateRequest
from typing import Dict, Any


def get_template(request: GenerateRequest) -> Dict[str, Any]:
    """
    Select and build the appropriate prompt template based on content type.
    """
    content_type = request.content_type.value
    
    if content_type == "blog_post":
        from app.prompts.blog import build_blog_post_prompt
        return build_blog_post_prompt(request)
    elif content_type == "email":
        from app.prompts.email import build_email_prompt
        return build_email_prompt(request)
    elif content_type == "social_media":
        from app.prompts.social_media import build_social_media_prompt
        return build_social_media_prompt(request)
    elif content_type == "linkedin":
        from app.prompts.linkedin import build_linkedin_prompt
        return build_linkedin_prompt(request)
    elif content_type == "job_application":
        from app.prompts.job_application import build_job_application_prompt
        return build_job_application_prompt(request)
    else:
        raise ValueError(f"Unsupported content type: {request.content_type}")
