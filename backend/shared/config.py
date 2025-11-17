"""Configuration management for all backend services."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # GCP Configuration
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    region: str = os.getenv("REGION", "europe-west1")
    environment: str = os.getenv("ENVIRONMENT", "dev")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://docai:password@localhost:5432/docai")
    db_password: str = os.getenv("DB_PASSWORD", "")

    # GCS Buckets
    gcs_bucket_uploads: str = os.getenv("GCS_BUCKET_UPLOADS", f"docai-uploads-dev")
    gcs_bucket_processed: str = os.getenv("GCS_BUCKET_PROCESSED", f"docai-processed-dev")
    gcs_bucket_temp: str = os.getenv("GCS_BUCKET_TEMP", f"docai-temp-dev")

    # Firebase
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")

    # Document AI
    documentai_location: str = os.getenv("DOCUMENTAI_LOCATION", "eu")
    documentai_id_processor_id: str = os.getenv("DOCUMENTAI_ID_PROCESSOR_ID", "")

    # Pub/Sub Topics
    pubsub_invoice_topic: str = "invoice-processing"
    pubsub_ocr_topic: str = "ocr-processing"
    pubsub_summarization_topic: str = "summarization-processing"
    pubsub_rag_ingestion_topic: str = "rag-ingestion"
    pubsub_rag_query_topic: str = "rag-query"
    pubsub_document_filling_topic: str = "document-filling"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
