"""Database connection and session management."""
"""Database configuration and session management."""

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
"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import get_settings

settings = get_settings()

# Create engine
# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.environment == "dev"
    echo=False
    max_overflow=10
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
def get_db():
    """Dependency for getting database session."""
# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Database session
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables)."""
def init_db() -> None:
    """Initialize database (create all tables)."""
    Base.metadata.create_all(bind=engine)
