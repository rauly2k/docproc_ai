"""Pydantic schemas for API request/response validation."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserSignupRequest(BaseModel):
    """User signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    tenant_name: str = Field(..., min_length=1, max_length=255)


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
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


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
    gcs_path: str
    gcs_processed_path: Optional[str]
    status: str
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]
    ocr_completed: bool
    invoice_parsed: bool
    summarized: bool
    rag_indexed: bool
    created_at: datetime
    updated_at: datetime

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
    quantity: Optional[float]
    unit_price: Optional[Decimal]
    amount: Decimal

    class Config:
        from_attributes = True


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
    invoice_date: Optional[date]
    due_date: Optional[date]
    subtotal: Optional[Decimal]
    tax_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    currency: str
    line_items: List[Dict[str, Any]]
    is_validated: bool
    validated_at: Optional[datetime]
    validation_notes: Optional[str]
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
    ocr_method: Optional[str] = "document-ai"


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
    model: Optional[str] = "gemini-1.5-flash"
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
    model: str = "gemini-1.5-flash"


class ChatSource(BaseModel):
    """Source chunk for RAG answer."""
    document_id: UUID
    chunk_index: int
    relevance_score: float
    content: str
    metadata: Optional[Dict[str, Any]] = {}


class ChatQueryResponse(BaseModel):
    """Response to chat query."""
    answer: str
    sources: List[ChatSource]
    model_used: str
    total_chunks_searched: int


class ChunkInfo(BaseModel):
    """Chunk information for debugging."""
    chunk_index: int
    content: str
    token_count: int
    metadata: Dict[str, Any]


class ChunksResponse(BaseModel):
    """Response with document chunks."""
    document_id: UUID
    total_chunks: int
    chunks: List[ChunkInfo]


# ============================================================================
# Document Filling Schemas
# ============================================================================

class DocumentFillingRequest(BaseModel):
    """Request to extract ID and fill PDF form."""
    document_id: UUID
    template_name: str


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


class TemplateInfo(BaseModel):
    """PDF template information."""
    name: str
    display_name: str
    description: Optional[str]
    required_fields: Optional[List[str]]


class TemplateListResponse(BaseModel):
    """List of available templates."""
    templates: List[TemplateInfo]


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
# Generic Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool
    message: str


class JobStatusResponse(BaseModel):
    """Async job status response."""
    job_id: str
    status: str
    message: str
    estimated_completion: Optional[datetime] = None


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
