import os
from pathlib import Path

from dotenv import load_dotenv

# Load env before any module that reads OPENROUTER_API_KEY at import time (e.g. app.ai_client).
_backend_dir = Path(__file__).resolve().parent.parent
_repo_root = _backend_dir.parent
load_dotenv(_repo_root / ".env")
load_dotenv(_backend_dir / ".env", override=True)


def _frontend_dist_path() -> Path:
    """Vite build under `frontend/dist`, or path from `GHOSTWRITER_FRONTEND_DIST`."""
    env = os.getenv("GHOSTWRITER_FRONTEND_DIST")
    if env:
        return Path(env).resolve()
    return (_repo_root / "frontend" / "dist").resolve()


import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import APIStatusError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from app.ai_client import AIClient
from app.cache import get_cache
from app.client_auth import ClientAuthMiddleware, extract_client_token, require_email_login
from app.email_auth import (
    SESSION_TTL,
    request_verification_code,
    revoke_session_token,
    session_email_for_token,
    verify_code_and_issue_session,
)
from app.env_validation import validate_production_config
from app.logging_config import setup_logging
from app.normalization import normalize_request, validate_request
from app.postprocess import post_process_content
from app.prompts import get_template
from app.quota import check_quota
from app.rate_limiter import get_rate_limiter
from app.schemas import (
    EmailAuthConfigResponse,
    EmailSendCodeRequest,
    EmailSendCodeResponse,
    EmailSessionResponse,
    EmailVerifyRequest,
    EmailVerifyResponse,
    ExportPDFRequest,
    GenerateRequest,
    GenerateResponse,
)
from app.utils import get_client_ip

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def _openrouter_error_message(exc: APIStatusError) -> str:
    """Full provider message for server-side logs only (bounded)."""
    try:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
    except Exception:
        pass
    return str(exc)[:500]


def _client_openrouter_detail(exc: APIStatusError) -> str:
    """Generic messages to clients; provider text is logged separately."""
    code = getattr(exc, "status_code", None) or 502
    if code == 401:
        return (
            "Invalid OpenRouter API key. Set OPENROUTER_API_KEY in backend/.env. "
            "Get a key at https://openrouter.ai/keys"
        )
    if code == 429:
        return "Rate limited by the AI provider. Try again later."
    if code >= 500:
        return "AI service is temporarily unavailable. Please try again later."
    if 400 <= code < 500:
        return "The AI service could not complete this request. Try again or adjust your input."
    return "AI service is temporarily unavailable. Please try again later."


# Initialize rate limiter and cache
rate_limiter = get_rate_limiter()
cache = get_cache()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_production_config()
    logger.info("Starting Ghostwriter API")
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


# Strip runs first (outermost), then ClientAuth, then CORS — paths are /generate before auth.
app.add_middleware(ClientAuthMiddleware)


class StripApiPrefixMiddleware(BaseHTTPMiddleware):
    """Rewrite `/api/...` to `/...` for a shared `/api` base URL behind proxies."""

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        if path.startswith("/api"):
            rest = path[len("/api") :]
            if not rest or rest == "/":
                new_path = "/"
            else:
                new_path = rest if rest.startswith("/") else "/" + rest
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode("utf-8")
        return await call_next(request)


app.add_middleware(StripApiPrefixMiddleware)

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
        "Response: %s %s - %s - %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )

    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ghostwriter"}


def _email_auth_public_config() -> EmailAuthConfigResponse:
    """Non-secret hints for the login UI (Resend vs local SMTP / Mailpit)."""
    backend = os.getenv("EMAIL_BACKEND", "smtp").strip().lower()
    eb: Literal["smtp", "resend"] = "resend" if backend == "resend" else "smtp"
    dev_inbox: str | None = None
    if eb == "smtp":
        host = os.getenv("SMTP_HOST", "localhost").strip().lower()
        if host in ("localhost", "127.0.0.1", "::1"):
            raw = os.getenv("MAILPIT_WEB_URL", "http://localhost:8025").strip()
            dev_inbox = raw or None
    return EmailAuthConfigResponse(
        require_email_login=require_email_login(),
        email_backend=eb,
        dev_inbox_url=dev_inbox,
    )


@app.get("/auth/email/config", response_model=EmailAuthConfigResponse)
async def auth_email_config():
    return _email_auth_public_config()


@app.post("/auth/email/send-code", response_model=EmailSendCodeResponse)
async def auth_email_send_code(body: EmailSendCodeRequest, http_request: Request):
    await request_verification_code(body.email, get_client_ip(http_request))
    return EmailSendCodeResponse()


@app.post("/auth/email/verify", response_model=EmailVerifyResponse)
async def auth_email_verify(body: EmailVerifyRequest, http_request: Request):
    token = await verify_code_and_issue_session(body.email, body.code, get_client_ip(http_request))
    return EmailVerifyResponse(access_token=token, expires_in=SESSION_TTL)


@app.get("/auth/email/session", response_model=EmailSessionResponse)
async def auth_email_session(http_request: Request):
    token = extract_client_token(http_request)
    email = await session_email_for_token(token or "")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or missing session.")
    return EmailSessionResponse(email=email)


@app.post("/auth/email/logout")
async def auth_email_logout(http_request: Request):
    token = extract_client_token(http_request)
    if token:
        await revoke_session_token(token)
    return {"message": "Signed out"}


@app.get("/metrics")
async def metrics():
    # Simple metrics endpoint
    return {
        "status": "ok",
        "cache_size": len(cache._cache) if hasattr(cache, "_cache") else 0,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(
    req: GenerateRequest, http_request: Request, background_tasks: BackgroundTasks
):
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
        raise HTTPException(
            status_code=429, detail="Daily quota exceeded. Please try again tomorrow."
        )

    # Normalize (ranges, blog word_target clamp), then validate with Pydantic
    try:
        normalized = normalize_request(req)
        validate_request(normalized)
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
        internal_msg = _openrouter_error_message(e)
        code = getattr(e, "status_code", None) or 502
        logger.error("OpenRouter API error (%s): %s", code, internal_msg, exc_info=True)
        client_detail = _client_openrouter_detail(e)
        if code == 401:
            raise HTTPException(status_code=401, detail=client_detail)
        if code == 429:
            raise HTTPException(status_code=429, detail=client_detail)
        if code in (400, 404) or (400 <= code < 500):
            raise HTTPException(status_code=code, detail=client_detail)
        if code >= 500:
            raise HTTPException(status_code=503, detail=client_detail)
        raise HTTPException(status_code=503, detail=client_detail)
    except Exception as e:
        error_msg = str(e)
        if (
            "invalid_api_key" in error_msg
            or "401" in error_msg
            or "Authentication" in str(type(e).__name__)
        ):
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid OpenRouter API key. Check OPENROUTER_API_KEY in the environment. "
                    "Get a key at https://openrouter.ai/keys"
                ),
            )
        if "OpenRouter client not initialized" in error_msg or "OPENROUTER_API_KEY" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "OpenRouter is not configured. Set OPENROUTER_API_KEY in the environment "
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
            ai_response["content"], normalized, ai_response.get("metadata", {})
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

        background_tasks.add_task(record_usage, client_ip, ai_response["metadata"]["tokens_used"])
        background_tasks.add_task(
            log_token_usage,
            client_ip,
            ai_response["metadata"]["tokens_used"],
            normalized.content_type.value,
            ai_response["metadata"].get("model", "unknown"),
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

    try:
        normalized = normalize_request(generate_request)
        validate_request(normalized)
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
        },
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

        pdf_name = f"ghostwriter-{request.content_type}-{int(time.time())}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf_name}"},
        )
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")


async def log_token_usage(client_ip: str, tokens: int, content_type: str, model: str):
    """Background task to log token usage for monitoring."""
    from app.logging_config import log_token_usage as log_token

    log_token(client_ip, tokens, content_type, model)


_spa_dist = _frontend_dist_path()
if _spa_dist.is_dir() and (_spa_dist / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(_spa_dist), html=True), name="spa")
else:

    @app.get("/")
    async def root_info():
        return {
            "service": "ghostwriter",
            "health": "/health",
            "docs": "/docs",
            "detail": (
                "API only — no frontend/dist. "
                "Build the SPA or set GHOSTWRITER_FRONTEND_DIST to serve the UI from this process."
            ),
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "An internal error occurred. Please try again later."}
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
