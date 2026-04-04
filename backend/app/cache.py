import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Cache:
    """
    Simple in-memory cache with TTL (Time To Live).
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            # Expired, remove it
            del self._cache[key]
            return None

        return entry["value"]

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
        }

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()


_cache_singleton: Cache | None = None


def get_cache() -> Cache:
    """Shared in-memory cache (singleton) for generation cache, email sessions, and codes."""
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = Cache()
    return _cache_singleton
