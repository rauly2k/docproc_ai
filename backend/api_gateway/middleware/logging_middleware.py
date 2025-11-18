"""Logging middleware for request/response tracking."""

import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.shared.logging_utils import (
    api_logger,
    request_id_var,
    tenant_id_var,
    user_id_var
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with structured logging."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Extract tenant_id and user_id from auth if available
        if hasattr(request.state, 'tenant_id'):
            tenant_id_var.set(request.state.tenant_id)
        if hasattr(request.state, 'user_id'):
            user_id_var.set(request.state.user_id)

        # Log request
        start_time = time.time()
        api_logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log response
            api_logger.info(
                f"Response {response.status_code}",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            api_logger.error(
                "Request failed",
                error=e,
                duration_ms=round(duration * 1000, 2)
            )
            raise
