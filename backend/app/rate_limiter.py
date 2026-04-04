import logging
import time
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.
    Limits requests per IP address.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    async def is_allowed(self, ip: str) -> bool:
        """
        Check if request from IP is allowed.
        Returns True if within rate limit, False otherwise.
        """
        now = time.time()

        # Clean old requests outside the window
        cutoff = now - self.window_seconds
        self.requests[ip] = [req_time for req_time in self.requests[ip] if req_time > cutoff]

        # Check if limit exceeded
        if len(self.requests[ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return False

        # Record this request
        self.requests[ip].append(now)
        return True


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    import os

    max_requests = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    return RateLimiter(max_requests=max_requests, window_seconds=window_seconds)


class KeyedRateLimiter:
    """In-memory rate limiter keyed by arbitrary string (IP, email, etc.)."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    async def is_allowed(self, key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        if len(self.requests[key]) >= self.max_requests:
            logger.warning("Keyed rate limit exceeded for key prefix: %s...", key[:16])
            return False
        self.requests[key].append(now)
        return True


_email_send_ip_limiter: KeyedRateLimiter | None = None
_email_send_email_limiter: KeyedRateLimiter | None = None
_email_verify_ip_limiter: KeyedRateLimiter | None = None


def get_email_send_ip_limiter() -> KeyedRateLimiter:
    global _email_send_ip_limiter
    if _email_send_ip_limiter is None:
        import os

        max_r = int(os.getenv("EMAIL_AUTH_SEND_IP_MAX", "10"))
        win = int(os.getenv("EMAIL_AUTH_SEND_IP_WINDOW_SECONDS", "900"))
        _email_send_ip_limiter = KeyedRateLimiter(max_requests=max_r, window_seconds=win)
    return _email_send_ip_limiter


def get_email_send_email_limiter() -> KeyedRateLimiter:
    global _email_send_email_limiter
    if _email_send_email_limiter is None:
        import os

        max_r = int(os.getenv("EMAIL_AUTH_SEND_EMAIL_MAX", "5"))
        win = int(os.getenv("EMAIL_AUTH_SEND_EMAIL_WINDOW_SECONDS", "3600"))
        _email_send_email_limiter = KeyedRateLimiter(max_requests=max_r, window_seconds=win)
    return _email_send_email_limiter


def get_email_verify_ip_limiter() -> KeyedRateLimiter:
    global _email_verify_ip_limiter
    if _email_verify_ip_limiter is None:
        import os

        max_r = int(os.getenv("EMAIL_AUTH_VERIFY_IP_MAX", "30"))
        win = int(os.getenv("EMAIL_AUTH_VERIFY_IP_WINDOW_SECONDS", "300"))
        _email_verify_ip_limiter = KeyedRateLimiter(max_requests=max_r, window_seconds=win)
    return _email_verify_ip_limiter
