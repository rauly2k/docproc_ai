"""SQLAlchemy database models."""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Date,
    Text, DECIMAL, ForeignKey, Index
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, DECIMAL, Date, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, VECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Date, Text, DECIMAL, ForeignKey, Index, JSONB
from sqlalchemy.dialects.postgresql import UUID, INET, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, Date, Numeric, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
"""SQLAlchemy database models for Anima X."""

import uuid
from datetime import datetime
from typing import Optional
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
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from .database import Base


class Tenant(Base):
    """Multi-tenant organization."""
    """Tenant table for multi-tenancy."""
    """Tenant model for multi-tenancy."""
    """Tenant table for multi-tenancy."""
    """Multi-tenant organization."""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})
    subdomain = Column(String(100), unique=True)  # e.g., "acme" for acme.animax.com
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    settings = Column(JSONB, default={})  # Tenant-specific config
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User account."""
    """User table (linked to Firebase Auth)."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    """User model."""

    __tablename__ = "users"
    __table_args__ = (
        Index('idx_firebase_uid', 'firebase_uid'),
        Index('idx_tenant_email', 'tenant_id', 'email', unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default='user')
    """User table linked to Firebase Auth."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")
    """User accounts linked to Firebase Auth."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, nullable=False)  # Firebase user ID
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # 'admin', 'user', 'viewer'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="user")

    # Indexes
    __table_args__ = (
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    __table_args__ = (
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),

class Document(Base):
    """Document model."""

    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_tenant_documents', 'tenant_id', 'created_at'),
        Index('idx_user_documents', 'user_id', 'created_at'),
        Index('idx_document_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """Uploaded document."""
    """Document table (all uploaded documents)."""
    """Documents table for all uploaded documents."""
    """All uploaded documents."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Metadata
    # Document metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    mime_type = Column(String(100))
    file_size_bytes = Column(BigInteger)
    document_type = Column(String(50))
    document_type = Column(String(50))  # 'invoice', 'contract', 'id', 'generic'

    # Storage
    gcs_path = Column(Text, nullable=False)
    gcs_processed_path = Column(Text)

    # Processing status
    status = Column(String(50), default="uploaded")
    status = Column(String(50), default="uploaded")  # 'uploaded', 'processing', 'completed', 'failed'
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    status = Column(String(50), default='uploaded')
    status = Column(String(50), default="uploaded")
    gcs_path = Column(Text, nullable=False)  # gs://bucket/path/to/file.pdf
    gcs_processed_path = Column(Text)  # For filled PDFs

    # Processing status
    status = Column(String(50), default="uploaded")  # 'uploaded', 'processing', 'completed', 'failed'
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)

    # AI processing flags
    ocr_completed = Column(Boolean, default=False)
    invoice_parsed = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    rag_indexed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    user = relationship("User", back_populates="documents")
    summary = relationship("DocumentSummary", back_populates="document", uselist=False)

    # Indexes
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    summaries = relationship("DocumentSummary", back_populates="document", cascade="all, delete-orphan")
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False)
    ocr_results = relationship("OCRResult", back_populates="document")
    summaries = relationship("DocumentSummary", back_populates="document")
    chunks = relationship("DocumentChunk", back_populates="document")


class InvoiceData(Base):
    """Invoice data extracted from documents."""

    __tablename__ = "invoice_data"
    __table_args__ = (
        Index('idx_tenant_invoices', 'tenant_id', 'invoice_date'),
        Index('idx_invoice_validation', 'is_validated'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False, cascade="all, delete-orphan")
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False)
    ocr_result = relationship("OCRResult", back_populates="document", uselist=False)
    summaries = relationship("DocumentSummary", back_populates="document")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    filling_result = relationship("DocumentFillingResult", back_populates="document", uselist=False)

    __table_args__ = (
        Index("idx_tenant_documents", "tenant_id", "created_at"),
        Index("idx_user_documents", "user_id", "created_at"),
        Index("idx_document_status", "status"),
    )


class DocumentSummary(Base):
    """Document summary."""
class DocumentChunk(Base):
    """Document chunks table for RAG (with vector embeddings)."""
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
    currency = Column(String(3), default='EUR')

    # Line items
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    subtotal = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Line items (stored as JSONB)
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)
    subtotal = Column(DECIMAL(15, 2))
    tax_amount = Column(DECIMAL(15, 2))
    total_amount = Column(DECIMAL(15, 2))
    currency = Column(String(3), default="EUR")

    # Line items (stored as JSONB for flexibility)
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)  # Full Document AI response

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="invoice_data")


class OCRResult(Base):
    """OCR results from documents."""

    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)

    extracted_text = Column(Text, nullable=False)
    confidence_score = Column(DECIMAL(5, 4))
    page_count = Column(Integer)
    ocr_method = Column(String(50))

    # Bounding boxes and layout (optional)
    layout_data = Column(JSONB)
    __table_args__ = (
        Index("idx_tenant_invoices", "tenant_id", "invoice_date"),
        Index("idx_invoice_validation", "is_validated"),
    )


class AuditLog(Base):
    """Audit logs for compliance."""
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
    model_used = Column(String(100))  # 'gemini-1.5-flash', 'claude-3-sonnet', etc.
    word_count = Column(Integer)
    key_points = Column(JSONB)  # Structured bullet points

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="summary")


class OCRResult(Base):
    """OCR text extraction result."""
    document = relationship("Document", back_populates="ocr_results")


class DocumentSummary(Base):
    """Document summaries."""

    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)

    summary = Column(Text, nullable=False)
    model_used = Column(String(100))
    word_count = Column(Integer)
    key_points = Column(JSONB)
    document = relationship("Document", back_populates="summaries")


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

    confidence_score = Column(DECIMAL(5, 4))  # 0.0 to 1.0
    page_count = Column(Integer)
    ocr_method = Column(String(50))  # 'document-ai', 'vision-api', 'gemini-vision'

    # Bounding boxes and layout (optional)
    layout_data = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit log for compliance."""
    # Relationships
    document = relationship("Document", back_populates="summaries")


class DocumentChunk(Base):
    """Document chunks for RAG."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index('idx_tenant_chunks', 'tenant_id'),
        Index('idx_document_chunks', 'document_id', 'chunk_index'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Vector embedding - note: actual vector type requires pgvector extension
    # embedding = Column(Vector(768))  # Uncomment when pgvector is installed

    metadata = Column(JSONB, default={})
    document = relationship("Document", back_populates="ocr_result")


class DocumentChunk(Base):
    """Document chunks for RAG (Retrieval-Augmented Generation)."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)  # Order of chunk in document
    content = Column(Text, nullable=False)
    token_count = Column(Integer)

    # Vector embedding (768 dimensions for textembedding-gecko)
    embedding = Column(VECTOR(768))
    embedding = Column(Vector(768))

    # Metadata for better retrieval
    metadata = Column(JSONB, default={})  # Page number, section, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime, default=datetime.utcnow)

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

class DocumentFillingResult(Base):
    """Document filling results (ID extraction + PDF filling)."""
    __table_args__ = (
        Index("idx_tenant_chunks", "tenant_id"),
        Index("idx_document_chunks", "document_id", "chunk_index"),
        Index("idx_embedding_hnsw", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}),
    )


class DocumentFillingResult(Base):
    """Results from ID extraction and PDF form filling."""

    __tablename__ = "document_filling_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)

    # Source document
    source_document_type = Column(String(50))

    # Extracted data
    extracted_fields = Column(JSONB, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Source document (ID card, etc.)
    source_document_type = Column(String(50))  # 'romanian_id', 'passport', etc.

    # Extracted data
    extracted_fields = Column(JSONB, nullable=False)  # {nume, prenume, cnp, etc.}

    # Filled PDF
    filled_pdf_gcs_path = Column(Text)
    template_used = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Audit logs for compliance."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_tenant', 'tenant_id', 'created_at'),
        Index('idx_audit_user', 'user_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))

    action = Column(String(100), nullable=False)
    # Relationships
    document = relationship("Document", back_populates="filling_result")


class AuditLog(Base):
    """Audit logs for compliance (GDPR, EU AI Act)."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))

    action = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)  # 'document_uploaded', 'invoice_processed', etc.
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
