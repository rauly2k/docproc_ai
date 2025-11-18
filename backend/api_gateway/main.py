"""API Gateway - Main FastAPI application."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import get_settings
from shared.auth import initialize_firebase

# Import routes
try:
    from routes import auth, documents, invoices, ocr, summaries, chat, filling, admin
except ImportError:
    # Fallback if routes directory structure is different
    try:
        from api_gateway.routes import auth, documents, invoices, ocr, summaries, chat, filling, admin
    except ImportError:
        print("Warning: Could not import all routes. Some endpoints may not be available.")
        auth = documents = invoices = ocr = summaries = chat = filling = admin = None

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting Document AI API Gateway...")
    try:
        initialize_firebase()
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️  Warning: Firebase initialization failed: {e}")

    yield

    # Shutdown
    print("👋 Shutting down Document AI API Gateway...")


# Create FastAPI app
app = FastAPI(
    title="Document AI API",
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


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
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
        "message": "Welcome to Document AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
if auth:
    app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
if documents:
    app.include_router(documents.router, prefix="/v1/documents", tags=["Documents"])
if invoices:
    app.include_router(invoices.router, prefix="/v1/invoices", tags=["Invoices"])
if ocr:
    app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])
if summaries:
    app.include_router(summaries.router, prefix="/v1/summaries", tags=["Summaries"])
if chat:
    app.include_router(chat.router, prefix="/v1/chat", tags=["Chat with PDF"])
if filling:
    app.include_router(filling.router, prefix="/v1/filling", tags=["Document Filling"])
if admin:
    app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
