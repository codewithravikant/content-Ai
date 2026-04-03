from pathlib import Path

from dotenv import load_dotenv

# Load env before any module that reads OPENROUTER_API_KEY at import time (e.g. app.ai_client).
_backend_dir = Path(__file__).resolve().parent.parent
_repo_root = _backend_dir.parent
load_dotenv(_repo_root / ".env")
load_dotenv(_backend_dir / ".env", override=True)

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any
import json

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
from app.debug_ndjson import dbg as _agent_dbg
from openai import APIStatusError
from fastapi.staticfiles import StaticFiles


class StripApiPrefixMiddleware(BaseHTTPMiddleware):
    """Rewrite /api/* to /* so production SPA (baseURL /api) hits existing routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if path == "/api" or path.startswith("/api/"):
            stripped = path[4:] or "/"
            request.scope["path"] = stripped
            request.scope["raw_path"] = stripped.encode("utf-8")
        return await call_next(request)


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def _openrouter_error_message(exc: APIStatusError) -> str:
    try:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
    except Exception:
        pass
    return str(exc)[:500]

# Initialize rate limiter and cache
rate_limiter = get_rate_limiter()
cache = get_cache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Ghostwriter API")
    # region agent log
    _agent_dbg(
        "H3",
        "main.lifespan",
        "cors_origins_ready",
        {"origin_count": len(allowed_origins), "has_env_cors": bool(os.getenv("CORS_ORIGINS"))},
    )
    # endregion
    yield
    # Shutdown
    logger.info("Shutting down Ghostwriter API")


app = FastAPI(
    title="Ghostwriter API",
    description="AI Content Generation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
# Browsers reject Access-Control-Allow-Origin: * together with credentialed requests.
# Default dev origins are explicit so localhost:3000 (Vite) can call localhost:8000 reliably.
import os
if os.getenv("CORS_ORIGINS"):
    allowed_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    if allowed_origins == ["*"]:
        allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI client
ai_client = AIClient()


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
    # region agent log
    _agent_dbg(
        "H3",
        "main.logging_middleware",
        "request_completed",
        {
            "method": request.method,
            "path": request.url.path,
            "origin": request.headers.get("origin"),
            "status_code": response.status_code,
        },
    )
    # endregion
    
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ghostwriter"}


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
    # region agent log
    _agent_dbg(
        "H5",
        "main.generate_content",
        "handler_entry",
        {
            "content_type": getattr(req.content_type, "value", str(req.content_type)),
            "origin": http_request.headers.get("origin"),
        },
    )
    # endregion
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
        logger.error("API key validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except APIStatusError as e:
        msg = _openrouter_error_message(e)
        code = getattr(e, "status_code", None) or 502
        logger.error("OpenRouter API error (%s): %s", code, msg, exc_info=True)
        if code == 401:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid OpenRouter API key. Set OPENROUTER_API_KEY in backend/.env. "
                    "Get a key at https://openrouter.ai/keys"
                ),
            )
        if code in (400, 404):
            raise HTTPException(status_code=code, detail=msg)
        if code == 429:
            raise HTTPException(status_code=429, detail=msg or "Rate limited. Try again later.")
        if 400 <= code < 500:
            raise HTTPException(status_code=code, detail=msg)
        raise HTTPException(status_code=503, detail=msg or "AI service error. Try again later.")
    except Exception as e:
        error_msg = str(e)
        if "invalid_api_key" in error_msg or "401" in error_msg or "Authentication" in str(type(e).__name__):
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid OpenRouter API key. Please check your OPENROUTER_API_KEY environment variable. "
                    "Get your API key from: https://openrouter.ai/keys"
                ),
            )
        if "OpenRouter client not initialized" in error_msg or "OPENROUTER_API_KEY" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "OpenRouter is not configured. Set OPENROUTER_API_KEY in backend/.env (or your environment) "
                    "and restart the server."
                ),
            )
        logger.error("AI generation error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later.",
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

    raw_text = (ai_response.get("content") or "").strip()
    if raw_text and not (processed.get("content") or "").strip():
        logger.warning("Post-processing removed all text; returning raw model output")
        processed = {
            "content": ai_response["content"].strip(),
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
            headers={"Content-Disposition": f"attachment; filename=ghostwriter-{request.content_type}-{int(time.time())}.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


async def log_token_usage(client_ip: str, tokens: int, content_type: str, model: str):
    """Background task to log token usage for monitoring."""
    from app.logging_config import log_token_usage as log_token
    log_token(client_ip, tokens, content_type, model)


# Monorepo Railway Nixpacks builds frontend/dist; serve SPA + /assets from same origin as API.
_frontend_dist = _repo_root / "frontend" / "dist"
if _frontend_dist.is_dir() and (_frontend_dist / "index.html").is_file():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="vite_assets")

    @app.get("/")
    async def root_spa():
        return FileResponse(_frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        safe_root = _frontend_dist.resolve()
        candidate = (safe_root / full_path).resolve()
        try:
            candidate.relative_to(safe_root)
        except ValueError:
            return FileResponse(_frontend_dist / "index.html")
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
else:

    @app.get("/")
    async def root():
        return {
            "service": "ghostwriter",
            "message": "Content AI API. Open /docs for the interactive API.",
            "docs": "/docs",
            "health": "/health",
            "openapi": "/openapi.json",
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


# Outermost middleware: strip /api before routing so /api/health → /health (see StripApiPrefixMiddleware).
app.add_middleware(StripApiPrefixMiddleware)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
