"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    environment: str = "development"
    debug: bool = False

    # GCP Project
    project_id: str
    region: str = "europe-west1"
    vertex_ai_location: str = "us-central1"

    # Database
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Cloud Storage Buckets
    gcs_bucket_uploads: str
    gcs_bucket_processed: str
    gcs_bucket_temp: str

    # Pub/Sub Topics
    pubsub_topic_invoice: str = "invoice-processing"
    pubsub_topic_ocr: str = "ocr-processing"
    pubsub_topic_summary: str = "summarization-processing"
    pubsub_topic_rag_ingest: str = "rag-ingestion"
    pubsub_topic_docfill: str = "document-filling"

    # Firebase
    firebase_credentials_path: str = ""
    firebase_project_id: str = ""

    # Document AI
    documentai_location: str = "eu"
    documentai_invoice_processor_id: str = ""
    documentai_ocr_processor_id: str = ""
    documentai_id_processor_id: str = ""

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_ssl: bool = False

    # Security
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    frontend_url: str = "http://localhost:3000"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # File Upload
    max_upload_size_mb: int = 50
    allowed_file_types: list[str] = ["application/pdf", "image/jpeg", "image/png"]

    # Sentry
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1

    # Feature Flags
    enable_invoice_processing: bool = True
    enable_ocr: bool = True
    enable_summarization: bool = True
    enable_rag: bool = True
    enable_document_filling: bool = True

    # AI Models
    gemini_flash_model: str = "gemini-1.5-flash"
    gemini_pro_model: str = "gemini-1.5-pro"
    embedding_model: str = "textembedding-gecko@003"

    # RAG Configuration
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_max_chunks: int = 5

    # Processing Timeouts (seconds)
    invoice_processing_timeout: int = 300
    ocr_processing_timeout: int = 600
    summarization_timeout: int = 300
    rag_ingestion_timeout: int = 900
    docfill_timeout: int = 300


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Initialize settings
settings = get_settings()
