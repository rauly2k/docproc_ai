"""Shared configuration management."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # GCP
    project_id: str = "docai-mvp-prod"
    region: str = "europe-west1"
    environment: str = "dev"

    # Database
    database_url: str = "postgresql://docai:password@localhost:5432/docai"
    cloud_sql_connection_name: str = ""
    db_user: str = "docai"
    db_password: str = ""
    db_name: str = "docai"

    # Storage
    gcs_bucket_uploads: str = "docai-mvp-prod-uploads-prod"
    gcs_bucket_processed: str = "docai-mvp-prod-processed-prod"
    gcs_bucket_temp: str = "docai-mvp-prod-temp-prod"

    # Pub/Sub
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summary: str = "summarization-processing"
    pubsub_topic_rag_ingest: str = "rag-ingestion"
    pubsub_topic_docfill: str = "document-filling"

    # Vertex AI
    vertex_ai_location: str = "us-central1"

    # Firebase
    firebase_project_id: str = "docai-mvp-prod"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
