"""API Gateway main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.shared.config import get_settings
from .routes import ocr

settings = get_settings()

app = FastAPI(
    title="Document AI API Gateway",
    description="API Gateway for Document AI Processing Platform",
    version="0.1.0"
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
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Document AI API Gateway",
        "version": "0.1.0",
        "docs": "/docs"
    }


# Include routers
app.include_router(ocr.router, prefix="/v1/ocr", tags=["OCR"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
