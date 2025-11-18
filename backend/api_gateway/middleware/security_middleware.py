"""Security middleware for headers and CORS."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # CSP header
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


def get_cors_middleware_config():
    """Get CORS middleware configuration."""
    environment = os.getenv('ENVIRONMENT', 'dev')

    allowed_origins = [
        os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        'http://localhost:5173',
        'http://localhost:3000',
    ]

    # Add production URLs in production
    if environment == 'production':
        prod_url = os.getenv('PRODUCTION_FRONTEND_URL')
        if prod_url:
            allowed_origins.append(prod_url)

    return {
        'allow_origins': allowed_origins,
        'allow_credentials': True,
        'allow_methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        'allow_headers': ['*'],
        'max_age': 3600,
    }


def get_trusted_hosts():
    """Get list of trusted hosts."""
    environment = os.getenv('ENVIRONMENT', 'dev')

    hosts = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
    ]

    # Add Cloud Run URLs
    api_url = os.getenv('API_GATEWAY_URL')
    if api_url:
        # Extract hostname from URL
        hostname = api_url.replace('https://', '').replace('http://', '').split('/')[0]
        hosts.append(hostname)

    # In development, allow all
    if environment == 'dev':
        return ['*']

    return hosts
