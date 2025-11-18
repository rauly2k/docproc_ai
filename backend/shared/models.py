"""SQLAlchemy database models for DocProc AI."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    DECIMAL,
    Date,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from .database import Base


class Tenant(Base):
    """Multi-tenant organization."""

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
    """User accounts linked to Firebase Auth."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_user_firebase_uid", "firebase_uid"),
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """All uploaded documents."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Document metadata
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
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False, cascade="all, delete-orphan")
    ocr_result = relationship("OCRResult", back_populates="document", uselist=False, cascade="all, delete-orphan")
    summaries = relationship("DocumentSummary", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    filling_result = relationship("DocumentFillingResult", back_populates="document", uselist=False, cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_documents", "tenant_id", "created_at"),
        Index("idx_user_documents", "user_id", "created_at"),
        Index("idx_document_status", "status"),
    )


class InvoiceData(Base):
    """Extracted invoice information."""

    __tablename__ = "invoice_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Vendor information
    vendor_name = Column(String(500))
    vendor_address = Column(Text)
    vendor_tax_id = Column(String(100))

    # Invoice details
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    due_date = Column(Date)

    # Amounts
    subtotal = Column(DECIMAL(15, 2))
    tax_amount = Column(DECIMAL(15, 2))
    total_amount = Column(DECIMAL(15, 2))
    currency = Column(String(3), default="EUR")

    # Line items (stored as JSONB for flexibility)
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    validation_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="invoice_data")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_invoices", "tenant_id", "invoice_date"),
        Index("idx_invoice_validation", "is_validated"),
    )


class OCRResult(Base):
    """OCR results for generic text extraction."""

    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    extracted_text = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(5, 4))
    page_count = Column(Integer)
    ocr_method = Column(String(50))

    # Bounding boxes and layout (optional)
    layout_data = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="ocr_result")


class DocumentSummary(Base):
    """Document summaries generated by AI."""

    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    summary = Column(Text, nullable=False)
    model_used = Column(String(100))
    word_count = Column(Integer)
    key_points = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="summaries")


class DocumentChunk(Base):
    """Document chunks for RAG (Retrieval-Augmented Generation)."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Vector embedding (768 dimensions for textembedding-gecko)
    embedding = Column(Vector(768))

    # Metadata for better retrieval
    metadata = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("idx_tenant_chunks", "tenant_id"),
        Index("idx_document_chunks", "document_id", "chunk_index"),
        # HNSW index for vector similarity search - created separately via migration
        # CREATE INDEX idx_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);
    )


class DocumentFillingResult(Base):
    """Results from ID extraction and PDF form filling."""

    __tablename__ = "document_filling_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Source document (ID card, etc.)
    source_document_type = Column(String(50))

    # Extracted data
    extracted_fields = Column(JSONB, nullable=False)

    # Filled PDF
    filled_pdf_gcs_path = Column(Text)
    template_used = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="filling_result")


class AuditLog(Base):
    """Audit logs for compliance (GDPR, EU AI Act)."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))

    action = Column(String(100), nullable=False)
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
