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
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Document Schemas =====

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str
    filename: str
    gcs_path: str
    created_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
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
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Chat/RAG Schemas =====

class ChatIndexRequest(BaseModel):
    document_id: UUID


class ChatQueryRequest(BaseModel):
    document_ids: List[UUID]
    question: str
    max_chunks: Optional[int] = 5


class ChatSource(BaseModel):
    document_id: UUID
    chunk_index: int
    relevance_score: float
    content: str


class ChatQueryResponse(BaseModel):
    answer: str
    sources: List[ChatSource]
    model_used: str


# ===== Document Filling Schemas =====

class DocumentFillingRequest(BaseModel):
    document_id: UUID  # ID card or source document
    template_name: str


class DocumentFillingResponse(BaseModel):
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
