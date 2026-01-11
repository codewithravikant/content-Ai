import logging
import sys
from pythonjsonlogger import jsonlogger
from typing import Dict, Any


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured logging with JSON formatter.
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


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
        }
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
        }
    )
