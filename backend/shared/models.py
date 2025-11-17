"""SQLAlchemy database models."""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Date,
    Text, DECIMAL, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from .database import Base


class Tenant(Base):
    """Multi-tenant organization."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user")

    # Indexes
    __table_args__ = (
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """Uploaded document."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    document_type = Column(String(50))

    # Storage
    gcs_path = Column(Text, nullable=False)
    gcs_processed_path = Column(Text)

    # Processing status
    status = Column(String(50), default="uploaded")
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)

    # AI processing flags
    ocr_completed = Column(Boolean, default=False)
    invoice_parsed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    rag_indexed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    user = relationship("User", back_populates="documents")
    summary = relationship("DocumentSummary", back_populates="document", uselist=False)

    # Indexes
    __table_args__ = (
        Index("idx_tenant_documents", "tenant_id", "created_at"),
        Index("idx_user_documents", "user_id", "created_at"),
        Index("idx_document_status", "status"),
    )


class DocumentSummary(Base):
    """Document summary."""
    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    summary = Column(Text, nullable=False)
    model_used = Column(String(100))
    word_count = Column(Integer)
    key_points = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="summary")


class OCRResult(Base):
    """OCR text extraction result."""
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    extracted_text = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(5, 4))
    page_count = Column(Integer)
    ocr_method = Column(String(50))

    layout_data = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit log for compliance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))

    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
