"""SQLAlchemy database models."""

from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, Date, Numeric, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


class Tenant(Base):
    """Tenant table for multi-tenancy."""
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
    """User table linked to Firebase Auth."""
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

    __table_args__ = (
        Index("idx_user_tenant_email", "tenant_id", "email", unique=True),
    )


class Document(Base):
    """Documents table for all uploaded documents."""
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
    invoice_data = relationship("InvoiceData", back_populates="document", uselist=False, cascade="all, delete-orphan")

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
    subtotal = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2))
    currency = Column(String(3), default="EUR")

    # Line items (stored as JSONB)
    line_items = Column(JSONB, default=[])

    # Raw extraction
    raw_extraction = Column(JSONB)

    # Human validation
    is_validated = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime)
    validation_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="invoice_data")

    __table_args__ = (
        Index("idx_tenant_invoices", "tenant_id", "invoice_date"),
        Index("idx_invoice_validation", "is_validated"),
    )


class AuditLog(Base):
    """Audit logs for compliance."""
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

    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
    )
