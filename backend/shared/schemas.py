"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Authentication schemas
class UserSignup(BaseModel):
    """User signup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    tenant_name: str


class UserLogin(BaseModel):
"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


# ===== Auth Schemas =====

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str


class UserLoginRequest(BaseModel):
"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


# Base schemas
class TenantBase(BaseModel):
    name: str
    subdomain: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantResponse(TenantBase):
    id: UUID
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    created_at: datetime
    is_active: bool
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
    """User response."""
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
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


# Document schemas
class DocumentUpload(BaseModel):
    """Document upload metadata."""
# ===== Document Schemas =====

class DocumentUploadResponse(BaseModel):
# Document schemas
class DocumentUpload(BaseModel):
    document_type: str = Field(..., pattern="^(invoice|contract|id|generic)$")


class DocumentResponse(BaseModel):
    """Document response."""
    id: UUID
    filename: str
    document_type: str
    status: str
    gcs_path: str
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    file_size_bytes: Optional[int]
    gcs_path: str
    rag_indexed: bool = False
    created_at: datetime
    updated_at: datetime
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
    id: UUID
    filename: str
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
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    document_type: Optional[str]
    gcs_path: str
    status: str
    created_at: datetime
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]
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


# Summary schemas
class SummaryRequest(BaseModel):
    """Request to generate summary."""
    model_preference: str = Field(default="auto", pattern="^(auto|flash|pro)$")
    summary_type: str = Field(default="concise", pattern="^(concise|detailed)$")
# Chat schemas
class ChatQueryRequest(BaseModel):
    """Request to query documents via chat."""
    question: str = Field(..., min_length=1, max_length=500)
    document_ids: Optional[List[UUID]] = None  # If None, search all documents
    max_chunks: int = Field(default=5, ge=1, le=10)
    model: str = Field(default="flash", pattern="^(flash|pro)$")


class ChatSource(BaseModel):
    """Source chunk for chat answer."""
    document_id: UUID
    chunk_index: int
    content: str
    relevance_score: float
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat response with answer and sources."""
    answer: str
    sources: List[ChatSource]
    model_used: str
    total_chunks_searched: int


# Summary schemas
class SummaryRequest(BaseModel):
    """Request to generate summary."""
    document_id: UUID
    use_premium: bool = False


class SummaryResponse(BaseModel):
    """Summary response."""
    id: UUID
    document_id: UUID
    summary: str
    key_points: List[str]
    word_count: int
    model_used: str
    model_used: str
    word_count: int
class DocumentListResponse(BaseModel):
# Invoice schemas
class LineItem(BaseModel):
    description: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[Decimal]
    amount: Optional[Decimal]

    class Config:
        from_attributes = True


class InvoiceDataResponse(BaseModel):
class DocumentListResponse(BaseModel):
    """Paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ===== Invoice Schemas =====

class LineItem(BaseModel):
    description: str
    quantity: Optional[float]
    unit_price: Optional[Decimal]
    amount: Decimal


class InvoiceDataResponse(BaseModel):
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
    invoice_date: Optional[date]
    due_date: Optional[date]
    invoice_date: Optional[datetime]
    due_date: Optional[datetime]
    subtotal: Optional[Decimal]
    tax_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    currency: str
    line_items: List[Dict[str, Any]]
    is_validated: bool
    line_items: List[LineItem]
    is_validated: bool
    validated_at: Optional[datetime]
    line_items: List[Dict[str, Any]]
    is_validated: bool
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceValidationRequest(BaseModel):
    corrections: Dict[str, Any]
    validation_notes: Optional[str]
    is_approved: bool


class InvoiceProcessRequest(BaseModel):
    document_id: UUID


# ===== OCR Schemas =====

class OCRExtractRequest(BaseModel):
    document_id: UUID
    method: Optional[str] = "auto"  # auto, documentai, vision, gemini


class OCRResultResponse(BaseModel):
    id: UUID
    document_id: UUID
    extracted_text: str
    confidence_score: Optional[float]
    page_count: Optional[int]
    ocr_method: Optional[str]
class InvoiceValidation(BaseModel):
    """Validation/correction data from user."""
    corrections: dict
class InvoiceValidationRequest(BaseModel):
    """Human validation/correction of invoice data."""
    corrections: Dict[str, Any]
    validation_notes: Optional[str] = None
    is_approved: bool


# Auth schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    tenant_name: str


class SignupResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID
    email: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
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


# ===== Summary Schemas =====

class SummaryGenerateRequest(BaseModel):
    document_id: UUID
    model: Optional[str] = "gemini-1.5-flash"  # gemini-1.5-flash, gemini-1.5-pro, claude-3-sonnet


class SummaryResponse(BaseModel):
    id: UUID
    document_id: UUID
    summary: str
    model_used: Optional[str]
    word_count: Optional[int]
    key_points: Optional[Dict[str, Any]]
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


# Chunk schemas
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
# ===== Chat/RAG Schemas =====

class ChatIndexRequest(BaseModel):
# ============================================================================
# Chat with PDF (RAG) Schemas
# ============================================================================

class ChatIndexRequest(BaseModel):
    """Request to index document for chat."""
    document_id: UUID


class ChatQueryRequest(BaseModel):
    document_ids: List[UUID]
    question: str
    max_chunks: Optional[int] = 5


class ChatSource(BaseModel):
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


# ===== Document Filling Schemas =====

class DocumentFillingRequest(BaseModel):
    document_id: UUID  # ID card or source document
    template_name: str


class DocumentFillingResponse(BaseModel):
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


# ===== Generic Responses =====

class JobStartedResponse(BaseModel):
    message: str
    document_id: UUID
    status: str = "processing"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str]
    status_code: int
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
