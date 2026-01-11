import time
import logging
from collections import defaultdict
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Simple quota manager for daily limits per IP.
    Tracks token usage and request counts.
    """
    
    def __init__(self, max_tokens_per_day: int = 50000, max_requests_per_day: int = 100):
        """
        Args:
            max_tokens_per_day: Maximum tokens allowed per IP per day
            max_requests_per_day: Maximum requests allowed per IP per day
        """
        self.max_tokens_per_day = max_tokens_per_day
        self.max_requests_per_day = max_requests_per_day
        self.daily_usage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "tokens": 0,
            "requests": 0,
            "reset_at": None,
        })
    
    async def check_quota(self, ip: str) -> bool:
        """
        Check if IP has quota remaining for today.
        Returns True if within quota, False otherwise.
        """
        now = datetime.now()
        usage = self.daily_usage[ip]
        
        # Reset if past midnight
        if usage["reset_at"] is None or now > usage["reset_at"]:
            usage["tokens"] = 0
            usage["requests"] = 0
            usage["reset_at"] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Check limits
        if usage["tokens"] >= self.max_tokens_per_day:
            logger.warning(f"Token quota exceeded for IP: {ip} ({usage['tokens']}/{self.max_tokens_per_day})")
            return False
        
        if usage["requests"] >= self.max_requests_per_day:
            logger.warning(f"Request quota exceeded for IP: {ip} ({usage['requests']}/{self.max_requests_per_day})")
            return False
        
        return True
    
    async def record_usage(self, ip: str, tokens: int) -> None:
        """Record token usage for an IP."""
        usage = self.daily_usage[ip]
        usage["tokens"] += tokens
        usage["requests"] += 1
    
    def get_usage(self, ip: str) -> Dict[str, Any]:
        """Get current usage for an IP."""
        usage = self.daily_usage[ip]
        return {
            "tokens": usage["tokens"],
            "requests": usage["requests"],
            "max_tokens": self.max_tokens_per_day,
            "max_requests": self.max_requests_per_day,
        }


# Global quota manager instance
_quota_manager: Optional[QuotaManager] = None


def get_quota_manager() -> QuotaManager:
    """Get quota manager instance."""
    global _quota_manager
    if _quota_manager is None:
        import os
        max_tokens = int(os.getenv("QUOTA_MAX_TOKENS_PER_DAY", "50000"))
        max_requests = int(os.getenv("QUOTA_MAX_REQUESTS_PER_DAY", "100"))
        _quota_manager = QuotaManager(max_tokens_per_day=max_tokens, max_requests_per_day=max_requests)
    return _quota_manager


async def check_quota(ip: str) -> bool:
    """Check if IP has quota remaining."""
    quota_manager = get_quota_manager()
    return await quota_manager.check_quota(ip)


async def record_usage(ip: str, tokens: int) -> None:
    """Record token usage for an IP."""
    quota_manager = get_quota_manager()
    await quota_manager.record_usage(ip, tokens)
