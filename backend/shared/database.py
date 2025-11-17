"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os

# Base class for models
Base = declarative_base()


def get_database_url() -> str:
    """Get database URL based on environment."""
    # Local development
    if os.getenv("ENVIRONMENT") == "dev":
        return os.getenv("DATABASE_URL", "postgresql://docai:password@localhost:5432/docai")

    # Production: use Cloud SQL connection string
    db_user = os.getenv("DB_USER", "docai")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "docai")
    connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    return f"postgresql://{db_user}:{db_password}@/{db_name}?host=/cloudsql/{connection_name}"


def create_database_engine():
    """Create SQLAlchemy engine."""
    database_url = get_database_url()
    echo = os.getenv("ENVIRONMENT") == "dev"
    return create_engine(database_url, echo=echo, poolclass=NullPool)


# Create engine
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
