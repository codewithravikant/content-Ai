import logging
import os
import sys
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


def _resolve_log_level_name() -> str:
    """
    Default WARNING (quiet). Use LOG_LEVEL=INFO or DEBUG for verbose output.
    GHOSTWRITER_DEBUG=1 is shorthand for DEBUG when LOG_LEVEL is unset.
    """
    explicit = os.getenv("LOG_LEVEL", "").strip()
    if explicit:
        return explicit.upper()
    if os.getenv("GHOSTWRITER_DEBUG", "").strip().lower() in ("1", "true", "yes"):
        return "DEBUG"
    return "WARNING"


def _level_from_name(name: str) -> int:
    level = getattr(logging, name.upper(), None)
    if isinstance(level, int):
        return level
    return logging.WARNING


def setup_logging(level: Optional[str] = None) -> None:
    """
    Setup structured logging with JSON formatter.

    Unless level is passed explicitly, reads LOG_LEVEL (default WARNING) or
    GHOSTWRITER_DEBUG=1 for DEBUG-level diagnostics (including postprocess detail).
    """
    level_name = (level or _resolve_log_level_name()).upper()
    root_level = _level_from_name(level_name)

    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)

    root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Uvicorn / FastAPI: match verbosity (quiet runs stay quiet)
    framework_level = logging.INFO if root_level <= logging.INFO else logging.WARNING
    logging.getLogger("uvicorn").setLevel(framework_level)
    logging.getLogger("uvicorn.error").setLevel(framework_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(framework_level)

    # HTTP client stacks (OpenRouter / httpx) — keep at WARNING unless debugging the stack
    for name in ("httpx", "httpcore", "openai", "http.client", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def log_request(request: Any, response: Any, process_time: float) -> None:
    """Log API request with structured data."""
    logger = logging.getLogger(__name__)
    logger.info(
        "API request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
        },
    )


def log_ai_error(error: Exception, context: Dict[str, Any]) -> None:
    """Log AI generation errors with context."""
    logger = logging.getLogger(__name__)
    logger.error(
        "AI generation error",
        extra={
            "error": str(error),
            "error_type": type(error).__name__,
            **context,
        },
        exc_info=True,
    )


def log_prompt_sizes_debug(system_chars: int, user_chars: int) -> None:
    """
    Safe diagnostics when LOG_LEVEL=DEBUG: character counts only.
    Never log system_prompt, user_prompt, or raw request bodies in shared environments.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Prompt sizes (chars): system=%s user=%s", system_chars, user_chars)


def log_token_usage(ip: str, tokens: int, content_type: str, model: str) -> None:
    """Log token usage for monitoring and cost tracking."""
    logger = logging.getLogger(__name__)
    logger.info(
        "Token usage",
        extra={
            "ip": ip,
            "tokens": tokens,
            "content_type": content_type,
            "model": model,
        },
    )
