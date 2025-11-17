"""API Gateway middleware (Phase 7.2 and 7.4)."""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from time import time

from backend.shared.logging import api_logger, request_id_var, tenant_id_var
from backend.shared.config import get_settings

settings = get_settings()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with structured logging (Phase 7.2)."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Extract tenant_id from auth if available
        if hasattr(request.state, 'tenant_id'):
            tenant_id_var.set(request.state.tenant_id)

        # Log request
        start_time = time()
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
            duration = time() - start_time

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
            duration = time() - start_time
            api_logger.error(
                "Request failed",
                error=e,
                duration_ms=round(duration * 1000, 2)
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers (Phase 7.4)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://apis.google.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://firebaseapp.com https://identitytoolkit.googleapis.com; "
            "frame-ancestors 'none';"
        )

        return response


def setup_cors(app):
    """Setup CORS middleware with strict origin checking."""
    allowed_origins = settings.cors_origins.copy()

    if settings.environment == "development":
        allowed_origins.extend([
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=3600
    )


def setup_trusted_hosts(app):
    """Setup trusted host middleware."""
    allowed_hosts = [
        "localhost",
        "127.0.0.1",
        "*.run.app",  # Cloud Run domains
    ]

    if settings.frontend_url:
        from urllib.parse import urlparse
        frontend_host = urlparse(settings.frontend_url).netloc
        if frontend_host:
            allowed_hosts.append(frontend_host)

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
