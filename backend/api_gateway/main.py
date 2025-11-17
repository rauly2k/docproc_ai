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
    }


# Include routers
app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
