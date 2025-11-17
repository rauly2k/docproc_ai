"""Redis caching layer (Phase 7.3)."""

import redis
import json
from typing import Optional, Any
from functools import wraps

from .config import get_settings

settings = get_settings()


class CacheManager:
    """Redis-based cache manager."""

    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                ssl=settings.redis_ssl,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            self.enabled = True
        except Exception as e:
            print(f"Redis connection failed: {e}. Caching disabled.")
            self.client = None
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 5 minutes)
        """
        if not self.enabled:
            return

        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {e}")

    def delete(self, key: str):
        """Delete key from cache."""
        if not self.enabled:
            return

        try:
            self.client.delete(key)
        except Exception:
            pass

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        if not self.enabled:
            return

        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception:
            pass

    def incr(self, key: str) -> int:
        """Increment counter."""
        if not self.enabled:
            return 0

        try:
            return self.client.incr(key)
        except Exception:
            return 0

    def expire(self, key: str, seconds: int):
        """Set expiration on key."""
        if not self.enabled:
            return

        try:
            self.client.expire(key, seconds)
        except Exception:
            pass


# Global cache instance
cache = CacheManager()


def cached(key_prefix: str, ttl: int = 300):
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds

    Usage:
        @cached(key_prefix="document", ttl=600)
        async def get_document(document_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args if arg)}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
