"""Configuration management for all backend services."""
"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings."""

    # GCP Settings
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    region: str = os.getenv("REGION", "europe-west1")
    environment: str = os.getenv("ENVIRONMENT", "dev")
    # Project settings
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    environment: str = os.getenv("ENVIRONMENT", "dev")
    region: str = os.getenv("REGION", "europe-west1")
"""Configuration management for Anima X services."""

import os
from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Anima X"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/docai_db"
    )
    db_password: str = os.getenv("DB_PASSWORD", "")

    # GCS Buckets
    gcs_bucket_uploads: str = f"docai-uploads-{environment}"
    gcs_bucket_processed: str = f"docai-processed-{environment}"
    gcs_bucket_temp: str = f"docai-temp-{environment}"
        "postgresql://docai:password@localhost:5432/docai"
    )

    # Google Cloud Storage
    gcs_bucket_uploads: str = os.getenv("GCS_BUCKET_UPLOADS", f"docai-uploads-{environment}")
    gcs_bucket_processed: str = os.getenv("GCS_BUCKET_PROCESSED", f"docai-processed-{environment}")
    gcs_bucket_temp: str = os.getenv("GCS_BUCKET_TEMP", f"docai-temp-{environment}")

    # Pub/Sub Topics
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summarization: str = "summarization-processing"
    pubsub_topic_summary: str = "summarization-processing"
    pubsub_topic_rag_ingest: str = "rag-ingestion"
    pubsub_topic_rag_query: str = "rag-query"
    pubsub_topic_docfill: str = "document-filling"

    # Document AI
    documentai_location: str = "us"
    documentai_invoice_processor_id: str = os.getenv("DOCUMENTAI_INVOICE_PROCESSOR_ID", "")
    documentai_ocr_processor_id: str = os.getenv("DOCUMENTAI_OCR_PROCESSOR_ID", "")
    documentai_id_processor_id: str = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID", "")

    # Vertex AI
    vertex_ai_location: str = "us-central1"

    # Firebase
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    # Security
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "")

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # API Settings
    api_title: str = "Document AI API"
    api_version: str = "1.0.0"
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]
        "postgresql://postgres:postgres@localhost:5432/animax_dev"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # GCP Project
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "animax-mvp-prod")
    gcp_region: str = os.getenv("GCP_REGION", "europe-west1")

    # Google Cloud Storage
    gcs_uploads_bucket: str = os.getenv("GCS_UPLOADS_BUCKET", "animax-uploads-dev")
    gcs_processed_bucket: str = os.getenv("GCS_PROCESSED_BUCKET", "animax-processed-dev")
    gcs_temp_bucket: str = os.getenv("GCS_TEMP_BUCKET", "animax-temp-dev")

    # Google Pub/Sub Topics
    pubsub_invoice_topic: str = "invoice-processing"
    pubsub_ocr_topic: str = "ocr-processing"
    pubsub_summarization_topic: str = "summarization-processing"
    pubsub_rag_ingestion_topic: str = "rag-ingestion"
    pubsub_rag_query_topic: str = "rag-query"
    pubsub_docfill_topic: str = "document-filling"
    pubsub_processing_complete_topic: str = "processing-complete"

    # Firebase
    firebase_credentials_path: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")

    # Vertex AI
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    vertex_ai_default_model: str = "gemini-1.5-flash"
    vertex_ai_embedding_model: str = "textembedding-gecko@003"

    # Document AI
    documentai_location: str = os.getenv("DOCUMENTAI_LOCATION", "eu")
    documentai_invoice_processor_id: Optional[str] = os.getenv("DOCUMENTAI_INVOICE_PROCESSOR_ID")
    documentai_ocr_processor_id: Optional[str] = os.getenv("DOCUMENTAI_OCR_PROCESSOR_ID")
    documentai_id_processor_id: Optional[str] = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID")

    # File Upload
    max_upload_size_mb: int = 10
    allowed_mime_types: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    # Security
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://animax.vercel.app"
    ]

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_day: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
