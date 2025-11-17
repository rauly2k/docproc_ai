"""Configuration management for Document AI services."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "dev")

    # GCP Configuration
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    region: str = os.getenv("REGION", "europe-west1")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://docai:password@localhost:5432/docai")

    # Google Cloud Storage
    gcs_bucket_uploads: str = os.getenv("GCS_BUCKET_UPLOADS", f"docai-uploads-{environment}")
    gcs_bucket_processed: str = os.getenv("GCS_BUCKET_PROCESSED", f"docai-processed-{environment}")
    gcs_bucket_temp: str = os.getenv("GCS_BUCKET_TEMP", f"docai-temp-{environment}")

    # Pub/Sub Topics
    pubsub_topic_invoice: str = os.getenv("PUBSUB_TOPIC_INVOICE", "invoice-processing")
    pubsub_topic_ocr: str = os.getenv("PUBSUB_TOPIC_OCR", "ocr-processing")
    pubsub_topic_summary: str = os.getenv("PUBSUB_TOPIC_SUMMARY", "summarization-processing")
    pubsub_topic_rag_ingest: str = os.getenv("PUBSUB_TOPIC_RAG_INGEST", "rag-ingestion")
    pubsub_topic_docfill: str = os.getenv("PUBSUB_TOPIC_DOCFILL", "document-filling")

    # Firebase
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", project_id)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
