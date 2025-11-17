"""SQLAlchemy database models."""

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, DECIMAL, Date, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, VECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from .database import Base


class Tenant(Base):
    """Tenant table for multi-tenancy."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    settings = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User table (linked to Firebase Auth)."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # 'admin', 'user', 'viewer'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user")

    __table_args__ = (
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """Document table (all uploaded documents)."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Document metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    document_type = Column(String(50))  # 'invoice', 'contract', 'id', 'generic'

    # Storage
    gcs_path = Column(Text, nullable=False)
    gcs_processed_path = Column(Text)

    # Processing status
    status = Column(String(50), default="uploaded")  # 'uploaded', 'processing', 'completed', 'failed'
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

    # AI processing flags
    ocr_completed = Column(Boolean, default=False)
    invoice_parsed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    rag_indexed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    summaries = relationship("DocumentSummary", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tenant_documents", "tenant_id", "created_at"),
        Index("idx_user_documents", "user_id", "created_at"),
        Index("idx_document_status", "status"),
    )


class DocumentChunk(Base):
    """Document chunks table for RAG (with vector embeddings)."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)  # Order of chunk in document
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Vector embedding (768 dimensions for textembedding-gecko)
    embedding = Column(VECTOR(768))

    # Metadata for better retrieval
    metadata = Column(JSONB, default={})  # Page number, section, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_tenant_chunks", "tenant_id"),
        Index("idx_document_chunks", "document_id", "chunk_index"),
        # HNSW index for vector similarity search - created separately after extension install
        # CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
    )


class DocumentSummary(Base):
    """Document summaries table."""
    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    summary = Column(Text, nullable=False)
    model_used = Column(String(100))  # 'gemini-1.5-flash', 'claude-3-sonnet', etc.
    word_count = Column(Integer)
    key_points = Column(JSONB)  # Structured bullet points

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="summaries")


class AuditLog(Base):
    """Audit logs table (for EU AI Act compliance)."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))

    action = Column(String(100), nullable=False)  # 'document_uploaded', 'invoice_processed', 'data_validated', etc.
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
