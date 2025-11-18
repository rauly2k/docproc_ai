"""Optimized database connection with connection pooling."""

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from backend.shared.config import get_settings

settings = get_settings()

# Optimized connection pool for Cloud Run
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,              # Small pool for serverless
    max_overflow=10,          # Allow burst
    pool_timeout=30,          # Connection timeout
    pool_recycle=1800,        # Recycle connections every 30 min
    pool_pre_ping=True,       # Test connections before use
    echo=False,               # Disable SQL logging in production
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
