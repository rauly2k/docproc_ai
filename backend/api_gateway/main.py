"""FastAPI API Gateway for Document AI SaaS."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from backend.shared.auth import init_firebase
from backend.shared.config import get_settings

settings = get_settings()

# Initialize Firebase
init_firebase()

# Create FastAPI app
app = FastAPI(
    title="Document AI API",
    description="AI-powered document processing platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
"""API Gateway main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import vertexai

from backend.shared.config import get_settings
from .routes import chat

settings = get_settings()

# Initialize Vertex AI
vertexai.init(project=settings.project_id, location=settings.vertex_ai_location)

# Create FastAPI app
app = FastAPI(
    title="Document AI API Gateway",
    version="1.0.0",
    description="AI-powered document processing platform"

from backend.shared.config import get_settings
from .routes import ocr

settings = get_settings()

app = FastAPI(
    title="Document AI API Gateway",
    description="API Gateway for Document AI Processing Platform",
    version="0.1.0"
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
    allow_origins=["*"],  # Configure this properly in production
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


# Include routers
from .routes import summaries

app.include_router(summaries.router, prefix="/v1/summaries", tags=["Summaries"])
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": settings.api_version
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Document AI API Gateway",
        "version": "0.1.0",
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


# Include routers
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat with PDF"])
@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Anima X API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])
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
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug
    )
