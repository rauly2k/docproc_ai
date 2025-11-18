"""Redis-based caching layer for API responses."""

import json
import os
from typing import Optional, Any
from functools import wraps

# Check if Redis is available
USE_REDIS = os.getenv('REDIS_HOST') is not None

if USE_REDIS:
    import redis
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
    except Exception:
        redis_client = None
        USE_REDIS = False
else:
    redis_client = None


class CacheManager:
    """Cache manager with Redis backend."""

    def __init__(self):
        self.client = redis_client
        self.enabled = USE_REDIS and redis_client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception:
            # Fail gracefully - cache miss on error
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)."""
        if not self.enabled:
            return

        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception:
            # Fail gracefully - don't break app on cache errors
            pass

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


# Global cache instance
cache = CacheManager()


def cached(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args)}"

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
