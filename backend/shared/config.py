"""Configuration management for all backend services."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings."""

    # GCP Settings
    project_id: str = os.getenv("PROJECT_ID", "docai-mvp-prod")
    region: str = os.getenv("REGION", "europe-west1")
    environment: str = os.getenv("ENVIRONMENT", "dev")

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

    # Pub/Sub Topics
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summarization: str = "summarization-processing"
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

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
