"""FastAPI API Gateway main application."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import sentry_sdk
from datetime import datetime

from backend.shared.config import get_settings
from backend.shared.database import check_db_connection
from backend.shared.cache import cache
from backend.shared.logging import api_logger
from .middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    setup_cors,
    setup_trusted_hosts
)

settings = get_settings()


# Initialize Sentry for error tracking (Phase 7.2)
if settings.sentry_dsn and settings.environment == "production":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.environment,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup/shutdown (Phase 7.3 optimization)."""
    # Startup
    api_logger.info("Starting API Gateway...")

    # Warm up database connection
    if check_db_connection():
        api_logger.info("Database connection successful")
    else:
        api_logger.error("Database connection failed")

    # Test Redis connection
    if cache.enabled:
        api_logger.info("Redis cache enabled")
    else:
        api_logger.warning("Redis cache disabled")

    api_logger.info("API Gateway ready")

    yield

    # Shutdown
    api_logger.info("Shutting down API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="Document AI SaaS API",
    description="Intelligent document processing API with OCR, invoice extraction, summarization, and RAG chat capabilities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "authentication", "description": "Authentication endpoints"},
        {"name": "documents", "description": "Document management"},
        {"name": "invoice", "description": "Invoice processing"},
        {"name": "ocr", "description": "OCR operations"},
        {"name": "summarization", "description": "Document summarization"},
        {"name": "chat", "description": "Chat with PDF (RAG)"},
        {"name": "filling", "description": "Document filling"},
        {"name": "feedback", "description": "Beta feedback"},
    ]
)

# Setup middleware
setup_cors(app)  # CORS - must be first
app.add_middleware(SecurityHeadersMiddleware)  # Security headers
app.add_middleware(LoggingMiddleware)  # Logging
setup_trusted_hosts(app)  # Trusted hosts


# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    api_logger.warning(
        "Validation error",
        errors=exc.errors(),
        body=exc.body
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    api_logger.error(
        "Unhandled exception",
        error=exc,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please try again later."
        }
    )


# Health check endpoint

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns system health status including database and cache connectivity.
    """
    db_healthy = check_db_connection()
    cache_healthy = cache.enabled

    health_status = {
        "status": "healthy" if db_healthy else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_healthy,
        "cache": cache_healthy,
        "environment": settings.environment
    }

    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Document AI SaaS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers (will be created separately)
# from .routes import documents, invoices, ocr, summaries, chat, filling, feedback
# app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
# app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoice"])
# app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["ocr"])
# app.include_router(summaries.router, prefix="/api/v1/summaries", tags=["summarization"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(filling.router, prefix="/api/v1/filling", tags=["filling"])
# app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        workers=4,
        log_level="info",
        access_log=True
    )
