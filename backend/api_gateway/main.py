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
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
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
        "version": "1.0.0"
    }


# Include routers
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat with PDF"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
