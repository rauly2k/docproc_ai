"""Configuration management for DocProc AI services."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    environment: str = os.getenv("ENVIRONMENT", "dev")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # GCP Configuration
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    region: str = os.getenv("REGION", "europe-west1")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://docai:password@localhost:5432/docai"
    )
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # Google Cloud Storage Buckets
    gcs_bucket_uploads: str = os.getenv("GCS_BUCKET_UPLOADS", f"docai-uploads-{os.getenv('ENVIRONMENT', 'dev')}")
    gcs_bucket_processed: str = os.getenv("GCS_BUCKET_PROCESSED", f"docai-processed-{os.getenv('ENVIRONMENT', 'dev')}")
    gcs_bucket_temp: str = os.getenv("GCS_BUCKET_TEMP", f"docai-temp-{os.getenv('ENVIRONMENT', 'dev')}")

    # Google Pub/Sub Topics
    pubsub_topic_invoice: str = os.getenv("PUBSUB_TOPIC_INVOICE", "invoice-processing")
    pubsub_topic_ocr: str = os.getenv("PUBSUB_TOPIC_OCR", "ocr-processing")
    pubsub_topic_summary: str = os.getenv("PUBSUB_TOPIC_SUMMARY", "summarization-processing")
    pubsub_topic_rag_ingest: str = os.getenv("PUBSUB_TOPIC_RAG_INGEST", "rag-ingestion")
    pubsub_topic_docfill: str = os.getenv("PUBSUB_TOPIC_DOCFILL", "document-filling")

    # Document AI
    documentai_location: str = os.getenv("DOCUMENTAI_LOCATION", "eu")
    documentai_invoice_processor_id: str = os.getenv("DOCUMENTAI_INVOICE_PROCESSOR_ID", "")
    documentai_ocr_processor_id: str = os.getenv("DOCUMENTAI_OCR_PROCESSOR_ID", "")
    documentai_id_processor_id: str = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID", "")

    # Vertex AI
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    vertex_ai_default_model: str = os.getenv("VERTEX_AI_DEFAULT_MODEL", "gemini-1.5-flash")
    vertex_ai_embedding_model: str = os.getenv("VERTEX_AI_EMBEDDING_MODEL", "textembedding-gecko@003")

    # Firebase
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", os.getenv("PROJECT_ID", "docai-mvp-prod"))
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    # API Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8080"))
    api_title: str = "Document AI API"
    api_version: str = "1.0.0"

    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]

    # File Upload
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    allowed_mime_types: list = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    # Security
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_per_day: int = int(os.getenv("RATE_LIMIT_PER_DAY", "1000"))

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
