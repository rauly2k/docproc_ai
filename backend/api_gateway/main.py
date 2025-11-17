"""API Gateway main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import filling

app = FastAPI(
    title="Document AI API Gateway",
    description="API Gateway for Document AI SaaS platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(filling.router, prefix="/v1/filling", tags=["Document Filling"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Document AI API Gateway",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
