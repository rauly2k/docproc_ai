"""Rate limiting using Redis (Phase 7.4)."""

from fastapi import HTTPException, Request
from typing import Callable
import time

from .cache import cache


class RateLimiter:
    """Token bucket rate limiter using Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client or cache.client

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Rate limit key (e.g., user_id or IP)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limited
        """
        if not self.redis:
            # If Redis unavailable, allow all requests
            return True

        try:
            current = int(time.time())
            window_key = f"rate_limit:{key}:{current // window_seconds}"

            # Increment counter
            count = self.redis.incr(window_key)

            # Set expiry on first request in window
            if count == 1:
                self.redis.expire(window_key, window_seconds)

            return count <= max_requests
        except Exception as e:
            print(f"Rate limit check error: {e}")
            # Fail open - allow request if Redis error
            return True


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints.

    Args:
        max_requests: Maximum requests per window
        window_seconds: Window size in seconds

    Usage:
        @router.post("/upload")
        @rate_limit(max_requests=10, window_seconds=60)
        async def upload_document(request: Request, ...):
            ...
    """
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            # Use IP address as rate limit key for unauthenticated requests
            client_ip = request.client.host if request.client else "unknown"

            # For authenticated requests, use user/tenant ID
            rate_key = f"ip:{client_ip}"
            if hasattr(request.state, 'user_id'):
                rate_key = f"user:{request.state.user_id}"
            elif hasattr(request.state, 'tenant_id'):
                rate_key = f"tenant:{request.state.tenant_id}"

            # Check rate limit
            if not rate_limiter.check_rate_limit(rate_key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window_seconds)}
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator
