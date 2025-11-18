"""Optimized FastAPI application with performance improvements."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.shared.database_optimized import engine, get_db
from backend.shared.cache import cache
from backend.shared.logging_utils import api_logger
from backend.api_gateway.middleware.logging_middleware import LoggingMiddleware
from backend.api_gateway.middleware.security_middleware import (
    SecurityHeadersMiddleware,
    get_cors_middleware_config
)
from starlette.middleware.cors import CORSMiddleware
from google.cloud import storage
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for warmup and shutdown."""
    # Startup: Warm up connections
    api_logger.info("Warming up application...")

    try:
        # Pre-initialize database connection
        with next(get_db()) as db:
            db.execute("SELECT 1")
        api_logger.info("Database connection warmed up")
    except Exception as e:
        api_logger.error("Failed to warm up database", error=e)

    try:
        # Pre-initialize GCS client
        storage_client = storage.Client()
        api_logger.info("GCS client initialized")
    except Exception as e:
        api_logger.error("Failed to initialize GCS client", error=e)

    try:
        # Pre-initialize Redis (if available)
        if cache.enabled:
            cache.client.ping()
            api_logger.info("Redis cache warmed up")
    except Exception as e:
        api_logger.error("Failed to warm up Redis", error=e)

    api_logger.info("Application ready")

    yield

    # Shutdown
    api_logger.info("Shutting down application...")


app = FastAPI(
    title="Document AI SaaS API",
    description="Intelligent document processing API with OCR, summarization, and chat capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "authentication", "description": "Authentication endpoints"},
        {"name": "documents", "description": "Document management"},
        {"name": "invoices", "description": "Invoice processing"},
        {"name": "ocr", "description": "OCR operations"},
        {"name": "summaries", "description": "Document summarization"},
        {"name": "chat", "description": "Chat with PDF (RAG)"},
        {"name": "filling", "description": "Document filling"},
        {"name": "admin", "description": "Admin operations"},
    ]
)

# Add middleware in correct order (last added = first executed)
# 1. CORS (first to handle preflight)
cors_config = get_cors_middleware_config()
app.add_middleware(CORSMiddleware, **cors_config)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Logging (last, so it sees the final request/response)
app.add_middleware(LoggingMiddleware)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }


@app.get("/", tags=["health"])
async def root():
    """Root endpoint."""
    return {
        "message": "Document AI SaaS API",
        "docs": "/docs",
        "version": "1.0.0"
    }


# Import and include routers
# Note: Import routes after app is created to avoid circular imports
from backend.api_gateway.routes import (
    auth,
    documents,
    invoices,
    ocr,
    summaries,
    chat,
    filling,
    admin
)

app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["documents"])
app.include_router(invoices.router, prefix="/v1/invoices", tags=["invoices"])
app.include_router(ocr.router, prefix="/v1/ocr", tags=["ocr"])
app.include_router(summaries.router, prefix="/v1/summaries", tags=["summaries"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(filling.router, prefix="/v1/filling", tags=["filling"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn

    # Run with multiple workers for better concurrency
    workers = int(os.getenv("WORKERS", 4))
    port = int(os.getenv("PORT", 8080))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )
