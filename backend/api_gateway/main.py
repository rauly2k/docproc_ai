"""API Gateway - Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.shared.config import get_settings
from routes import invoices

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI-powered document processing API"
"""
Anima X API Gateway - Main FastAPI application.

This is the central API gateway for the Anima X document processing platform.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings
from shared.auth import initialize_firebase
from shared.database import init_db

# Import routes
from routes import auth, documents, invoices, ocr, summaries, chat, filling, admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting Anima X API Gateway...")
    initialize_firebase()
    print("✅ Firebase initialized")

    # Note: In production, database migrations should be run separately
    # For development, you can uncomment the line below
    # init_db()

    yield

    # Shutdown
    print("👋 Shutting down Anima X API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="Anima X API",
    description="AI-Powered Document Processing Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": settings.api_version
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Document AI API",
        "version": settings.api_version,
        "docs_url": "/docs"
# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "status_code": 500
        }
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Anima X API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])
app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])
app.include_router(summaries.router, prefix="/v1/summaries", tags=["Summaries"])
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat with PDF"])
app.include_router(filling.router, prefix="/v1/filling", tags=["Document Filling"])
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug
    )
