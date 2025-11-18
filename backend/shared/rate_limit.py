"""Rate limiting middleware and utilities."""

import time
from typing import Callable
from fastapi import HTTPException, Request
from backend.shared.cache import cache


class RateLimiter:
    """Token bucket rate limiter using Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client or (cache.client if cache.enabled else None)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit.
        Returns True if allowed, False if rate limited.
        """
        if not self.redis:
            # No Redis - allow all requests
            return True

        current = int(time.time())
        window_key = f"rate_limit:{key}:{current // window_seconds}"

        try:
            # Increment counter
            count = self.redis.incr(window_key)

            # Set expiry on first request in window
            if count == 1:
                self.redis.expire(window_key, window_seconds * 2)

            return count <= max_requests
        except Exception:
            # On error, allow request
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting endpoints."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)

            # Use IP address as rate limit key
            client_ip = request.client.host if request.client else "unknown"

            # For authenticated requests, use user ID
            if hasattr(request.state, 'user_id'):
                rate_key = f"user:{request.state.user_id}"
            else:
                rate_key = f"ip:{client_ip}"

            # Check rate limit
            if not rate_limiter.check_rate_limit(rate_key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window_seconds)}
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
