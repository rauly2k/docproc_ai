"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings."""

    # Project settings
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    environment: str = os.getenv("ENVIRONMENT", "dev")
    region: str = os.getenv("REGION", "europe-west1")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://docai:password@localhost:5432/docai"
    )

    # Google Cloud Storage
    gcs_bucket_uploads: str = os.getenv("GCS_BUCKET_UPLOADS", f"docai-uploads-{environment}")
    gcs_bucket_processed: str = os.getenv("GCS_BUCKET_PROCESSED", f"docai-processed-{environment}")
    gcs_bucket_temp: str = os.getenv("GCS_BUCKET_TEMP", f"docai-temp-{environment}")

    # Pub/Sub Topics
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summary: str = "summarization-processing"
    pubsub_topic_rag_ingest: str = "rag-ingestion"
    pubsub_topic_rag_query: str = "rag-query"
    pubsub_topic_docfill: str = "document-filling"

    # Document AI
    documentai_location: str = "us"

    # API Settings
    api_title: str = "Document AI API"
    api_version: str = "1.0.0"
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
