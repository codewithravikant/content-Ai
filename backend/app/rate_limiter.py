import time
import logging
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
