"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserSignupRequest(BaseModel):
    """User signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None  # For creating new tenant


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User information response."""
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: UUID
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: UUID
    status: str
    filename: str
    gcs_path: str
    created_at: datetime


class DocumentMetadata(BaseModel):
    """Document metadata update."""
    document_type: Optional[str] = None
    filename: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document details response."""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    filename: str
    original_filename: Optional[str]
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    document_type: Optional[str]
    status: str
    ocr_completed: bool
    invoice_parsed: bool
    summarized: bool
    rag_indexed: bool
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Invoice Schemas
# ============================================================================

class LineItem(BaseModel):
    """Invoice line item."""
    description: str
    quantity: float
    unit_price: Decimal
    amount: Decimal


class InvoiceProcessRequest(BaseModel):
    """Request to process an invoice."""
    document_id: UUID


class InvoiceDataResponse(BaseModel):
    """Extracted invoice data."""
    id: UUID
    document_id: UUID
    vendor_name: Optional[str]
    vendor_address: Optional[str]
    vendor_tax_id: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[datetime]
    due_date: Optional[datetime]
    subtotal: Optional[Decimal]
    tax_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    currency: str
    line_items: List[Dict[str, Any]]
    is_validated: bool
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceValidationRequest(BaseModel):
    """Human validation/correction of invoice data."""
    corrections: Dict[str, Any]
    validation_notes: Optional[str] = None
    is_approved: bool


# ============================================================================
# OCR Schemas
# ============================================================================

class OCRExtractRequest(BaseModel):
    """Request to extract text from document."""
    document_id: UUID
    ocr_method: Optional[str] = "document-ai"  # 'document-ai', 'vision-api', 'gemini-vision'


class OCRResultResponse(BaseModel):
    """OCR extraction result."""
    id: UUID
    document_id: UUID
    extracted_text: str
    confidence_score: Optional[Decimal]
    page_count: Optional[int]
    ocr_method: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Summarization Schemas
# ============================================================================

class SummarizationRequest(BaseModel):
    """Request to generate document summary."""
    document_id: UUID
    model: Optional[str] = "gemini-1.5-flash"  # Model to use
    max_words: Optional[int] = 200


class SummaryResponse(BaseModel):
    """Document summary response."""
    id: UUID
    document_id: UUID
    summary: str
    model_used: str
    word_count: Optional[int]
    key_points: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Chat with PDF (RAG) Schemas
# ============================================================================

class ChatIndexRequest(BaseModel):
    """Request to index document for chat."""
    document_id: UUID


class ChatQueryRequest(BaseModel):
    """Request to query documents."""
    document_ids: List[UUID]
    question: str
    max_chunks: int = 5


class ChatSource(BaseModel):
    """Source chunk for RAG answer."""
    document_id: UUID
    chunk_index: int
    relevance_score: float
    content: str


class ChatQueryResponse(BaseModel):
    """Response to chat query."""
    answer: str
    sources: List[ChatSource]
    model_used: str


# ============================================================================
# Document Filling Schemas
# ============================================================================

class DocumentFillingRequest(BaseModel):
    """Request to extract ID and fill PDF form."""
    document_id: UUID  # ID card/document to extract from
    template_name: str  # PDF template to fill


class DocumentFillingResponse(BaseModel):
    """Document filling result."""
    id: UUID
    document_id: UUID
    source_document_type: str
    extracted_fields: Dict[str, Any]
    filled_pdf_gcs_path: Optional[str]
    template_used: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Admin Schemas
# ============================================================================

class TenantStatsResponse(BaseModel):
    """Tenant usage statistics."""
    tenant_id: UUID
    total_documents: int
    total_invoices_processed: int
    total_ocr_processed: int
    total_summaries_generated: int
    total_rag_queries: int
    storage_used_bytes: int


class UserRoleUpdateRequest(BaseModel):
    """Update user role."""
    role: str = Field(..., pattern="^(admin|user|viewer)$")


# ============================================================================
# Pub/Sub Message Schemas
# ============================================================================

class PubSubJobMessage(BaseModel):
    """Standard Pub/Sub job message format."""
    tenant_id: str
    user_id: str
    document_id: str
    gcs_path: str
    document_type: str
    options: Optional[Dict[str, Any]] = {}
    callback_url: Optional[str] = None


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# Generic Response Schemas
# ============================================================================

class JobStatusResponse(BaseModel):
    """Async job status response."""
    job_id: str
    status: str  # 'processing', 'completed', 'failed'
    message: str
    estimated_completion: Optional[datetime] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str
