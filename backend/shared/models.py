"""SQLAlchemy database models."""

from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Float, Text,
    JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import enum

from .database import Base


class DocumentType(str, enum.Enum):
    """Document types."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    ID_CARD = "id_card"
    PASSPORT = "passport"
    GENERIC = "generic"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, enum.Enum):
    """Processing job status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, enum.Enum):
    """Processing job types."""
    INVOICE_EXTRACTION = "invoice_extraction"
    OCR = "ocr"
    SUMMARIZATION = "summarization"
    RAG_INGESTION = "rag_ingestion"
    DOCUMENT_FILLING = "document_filling"


# Models

class Tenant(Base):
    """Tenant/Organization model for multi-tenancy."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    firebase_uid = Column(String(255), unique=True, nullable=False, index=True)

    subscription_tier = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")


class Document(Base):
    """Document model."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    filename = Column(String(500), nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)

    gcs_uri = Column(Text, nullable=False)
    mime_type = Column(String(100))
    file_size_bytes = Column(Integer)

    ocr_text = Column(Text)
    page_count = Column(Integer)

    metadata = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False, cascade="all, delete-orphan")
    document_summary = relationship("DocumentSummary", back_populates="document", uselist=False, cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_documents_tenant_created", "tenant_id", "created_at"),
        Index("idx_documents_tenant_status", "tenant_id", "status"),
        Index("idx_documents_tenant_type", "tenant_id", "document_type"),
    )


class ProcessingJob(Base):
    """Processing job model."""
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)

    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    processing_time_ms = Column(Integer)
    retry_count = Column(Integer, default=0)

    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="processing_jobs")

    __table_args__ = (
        Index("idx_jobs_tenant_created", "tenant_id", "created_at"),
        Index("idx_jobs_document_status", "document_id", "status"),
    )


class InvoiceData(Base):
    """Extracted invoice data."""
    __tablename__ = "invoice_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Invoice fields
    supplier_name = Column(String(500))
    supplier_address = Column(Text)
    supplier_vat = Column(String(100))

    invoice_number = Column(String(100))
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)

    currency = Column(String(10))
    subtotal = Column(Float)
    tax_amount = Column(Float)
    total_amount = Column(Float)

    line_items = Column(JSON)  # Array of line items

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_at = Column(DateTime)
    validated_by = Column(String(255))

    confidence_score = Column(Float)
    raw_extraction = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="invoice_data")


class DocumentSummary(Base):
    """Document summary."""
    __tablename__ = "document_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    summary = Column(Text, nullable=False)
    key_points = Column(ARRAY(Text))

    word_count = Column(Integer)
    model_used = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="document_summary")


class DocumentChunk(Base):
    """Document chunks for RAG."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    token_count = Column(Integer)
    page_number = Column(Integer)

    embedding = Column(Vector(768))  # Gecko embedding dimension

    metadata = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="document_chunks")

    __table_args__ = (
        Index("idx_chunks_tenant_document", "tenant_id", "document_id"),
        # HNSW index for vector similarity search (created in migration)
    )


class ChatSession(Base):
    """Chat session for RAG queries."""
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    document_ids = Column(ARRAY(UUID(as_uuid=True)))
    title = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message."""
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    sources = Column(JSON)  # Source chunks used for answer
    model_used = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_session_created", "session_id", "created_at"),
    )


class AuditLog(Base):
    """Audit log for compliance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255))

    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))

    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(Text)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_audit_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_audit_user_action", "user_id", "action"),
    )
