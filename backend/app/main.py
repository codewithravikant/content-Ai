from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any
import json
import os
from pathlib import Path

from app.schemas import GenerateRequest, GenerateResponse, ExportPDFRequest
from app.normalization import normalize_request, validate_request
from app.prompts import get_template
from app.ai_client import AIClient
from app.postprocess import post_process_content
from app.logging_config import setup_logging
from app.rate_limiter import get_rate_limiter
from app.cache import get_cache
from app.quota import check_quota
from app.utils import get_client_ip

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize rate limiter and cache
rate_limiter = get_rate_limiter()
cache = get_cache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Content AI API")
    yield
    # Shutdown
    logger.info("Shutting down Content AI API")


app = FastAPI(
    title="Content AI API",
    description="AI Content Generation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
# Get allowed origins from environment variable or default to wildcard
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, set CORS_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI client
ai_client = AIClient()

# Mount static files for frontend (only if frontend/dist exists)
# This allows single-service deployment from root directory
_frontend_dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _frontend_dist_path.exists():
    # Mount static files at root, but exclude API routes
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist_path / "assets")), name="assets")
    logger.info(f"Mounted frontend static files from {_frontend_dist_path}")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "content-ai"}


@app.get("/metrics")
async def metrics():
    # Simple metrics endpoint
    return {
        "status": "ok",
        "cache_size": len(cache._cache) if hasattr(cache, '_cache') else 0,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(req: GenerateRequest, http_request: Request, background_tasks: BackgroundTasks):
    """
    Generate content based on user input.
    Includes validation, normalization, prompt generation, AI call, and post-processing.
    """
    client_ip = get_client_ip(http_request)
    
    # Rate limiting
    if not await rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    # Quota checking
    if not await check_quota(client_ip):
        logger.warning(f"Quota exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Daily quota exceeded. Please try again tomorrow.")
    
    # Validate and normalize request
    try:
        validated = validate_request(req)
        normalized = normalize_request(validated)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check cache
    cache_key = f"{normalized.content_type}:{hash(str(normalized.model_dump()))}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for key: {cache_key}")
        return GenerateResponse(**cached)
    
    # Get prompt template
    try:
        prompt_data = get_template(normalized)
    except Exception as e:
        logger.error(f"Template error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prompt template")
    
    # Call AI service
    start_time = time.time()
    try:
        ai_response = await ai_client.generate_stream(normalized, prompt_data)
    except ValueError as e:
        # Handle API key validation errors
        logger.error(f"API key validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        # Provide better error messages for common authentication issues
        if "invalid_api_key" in error_msg or "401" in error_msg or "Authentication" in str(type(e).__name__):
            if "AIza" in error_msg or os.getenv("OPENAI_API_KEY", "").startswith("AIza"):
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "Invalid API key: You're using a Google API key instead of an OpenAI API key. "
                        "OpenAI API keys start with 'sk-' or 'sk-proj-'. "
                        "Get your OpenAI API key from: https://platform.openai.com/account/api-keys"
                    )
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable. "
                        "Get your API key from: https://platform.openai.com/account/api-keys"
                    )
                )
        raise
    except Exception as e:
        logger.error(f"AI generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later."
        )
    
    generation_time = time.time() - start_time
    logger.info(f"AI generation completed in {generation_time:.3f}s")
    
    # Post-process content
    try:
        processed = post_process_content(
            ai_response["content"],
            normalized,
            ai_response.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Post-processing error: {e}")
        # Return raw content if post-processing fails
        processed = {
            "content": ai_response["content"],
            "metadata": ai_response.get("metadata", {}),
        }
    
    # Log token usage in background
    if "tokens_used" in ai_response.get("metadata", {}):
        from app.quota import record_usage
        background_tasks.add_task(
            record_usage,
            client_ip,
            ai_response["metadata"]["tokens_used"]
        )
        background_tasks.add_task(
            log_token_usage,
            client_ip,
            ai_response["metadata"]["tokens_used"],
            normalized.content_type.value,
            ai_response["metadata"].get("model", "unknown")
        )
    
    # Cache result
    result = {
        "content": processed["content"],
        "metadata": processed.get("metadata", {}),
    }
    await cache.set(cache_key, result, ttl=3600)  # Cache for 1 hour
    
    # Build response with proper metadata structure
    from app.schemas import ContentMetadata
    metadata_dict = processed.get("metadata", {})
    metadata = None
    if metadata_dict:
        try:
            metadata = ContentMetadata(**metadata_dict)
        except Exception as e:
            logger.warning(f"Failed to create metadata object: {e}")
            # Create with minimal fields
            metadata = ContentMetadata(
                word_count=metadata_dict.get("word_count"),
                tokens_used=metadata_dict.get("tokens_used"),
            )
    
    return GenerateResponse(content=processed["content"], metadata=metadata)


@app.get("/generate/stream")
async def generate_content_stream(http_request: Request):
    """
    Stream content generation using Server-Sent Events (SSE).
    Provides real-time feedback as content is generated.
    """
    try:
        # Parse request from query params
        data_param = http_request.query_params.get("data")
        if not data_param:
            raise HTTPException(status_code=400, detail="Missing data parameter")
        
        generate_request = GenerateRequest(**json.loads(data_param))
    except Exception as e:
        logger.error(f"Stream request parsing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request data")
    
    client_ip = get_client_ip(http_request)
    
    # Rate limiting
    if not await rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Quota checking
    if not await check_quota(client_ip):
        raise HTTPException(status_code=429, detail="Daily quota exceeded")
    
    # Validate and normalize
    try:
        validated = validate_request(generate_request)
        normalized = normalize_request(validated)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Get prompt template
    try:
        prompt_data = get_template(normalized)
    except Exception as e:
        logger.error(f"Template error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prompt template")
    
    async def generate_stream():
        try:
            async for chunk in ai_client.generate_stream_chunks(normalized, prompt_data):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            error_msg = json.dumps({"error": "Generation failed"})
            yield f"data: {error_msg}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/export/pdf")
async def export_pdf(request: ExportPDFRequest):
    """
    Export content to PDF format (backend rendering).
    """
    from app.pdf_export import generate_pdf
    
    try:
        pdf_bytes = await generate_pdf(request.content, request.content_type)
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=content-ai-{request.content_type}-{int(time.time())}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


async def log_token_usage(client_ip: str, tokens: int, content_type: str, model: str):
    """Background task to log token usage for monitoring."""
    from app.logging_config import log_token_usage as log_token
    log_token(client_ip, tokens, content_type, model)


@app.get("/")
async def serve_index():
    """Serve frontend index.html at root."""
    index_path = _frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """
    Serve frontend SPA - catch-all route for client-side routing.
    Only serves frontend if it's not an API route.
    """
    # Don't interfere with API routes
    if full_path.startswith(("api/", "generate", "export", "health", "metrics", "docs", "openapi.json")):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve index.html for SPA routing
    index_path = _frontend_dist_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    # If no frontend, return 404
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
