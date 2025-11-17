"""Pydantic schemas for request/response validation (Phase 7.4)."""

from pydantic import BaseModel, Field, validator, constr
from typing import Optional, List
from datetime import datetime
import re
import uuid


# Document Schemas

class DocumentUpload(BaseModel):
    """Validated document upload request."""

    filename: constr(min_length=1, max_length=255) = Field(
        ...,
        description="Original filename"
    )

    document_type: str = Field(
        ...,
        description="Type of document"
    )

    @validator('filename')
    def validate_filename(cls, v):
        """Sanitize filename - prevent path traversal."""
        # Remove any path components
        v = v.split('/')[-1].split('\\')[-1]

        # Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Filename contains invalid characters')

        # Check extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File type not allowed. Allowed: {allowed_extensions}')

        return v

    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type is from allowed list."""
        allowed_types = ['invoice', 'receipt', 'contract', 'id_card', 'passport', 'generic']
        if v not in allowed_types:
            raise ValueError(f'Invalid document type. Allowed: {allowed_types}')
        return v


class DocumentResponse(BaseModel):
    """Document response model."""
    id: uuid.UUID
    filename: str
    document_type: str
    status: str
    gcs_uri: str
    created_at: datetime

    class Config:
        from_attributes = True


# Invoice Schemas

class InvoiceUpdate(BaseModel):
    """Validated invoice update request."""

    supplier_name: Optional[constr(max_length=200)] = None
    invoice_number: Optional[constr(max_length=100)] = None
    total_amount: Optional[float] = Field(None, ge=0, le=999999999)
    is_validated: Optional[bool] = None

    @validator('total_amount')
    def validate_amount(cls, v):
        """Ensure reasonable amount."""
        if v is not None and (v < 0 or v > 999999999):
            raise ValueError('Amount out of reasonable range')
        return v


# Chat Schemas

class ChatMessage(BaseModel):
    """Validated chat message."""

    message: constr(min_length=1, max_length=5000) = Field(
        ...,
        description="User message"
    )

    document_ids: Optional[List[uuid.UUID]] = Field(
        None,
        description="Document IDs to query"
    )

    @validator('message')
    def validate_message(cls, v):
        """Sanitize message - prevent injection."""
        # Remove null bytes
        v = v.replace('\x00', '')

        # Check for suspicious patterns (basic SQL injection detection)
        suspicious_patterns = [
            r'(union\s+select)',
            r'(insert\s+into)',
            r'(delete\s+from)',
            r'(drop\s+table)',
            r'(<script)',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contains prohibited content')

        return v.strip()


class ChatQueryRequest(BaseModel):
    """Chat query request."""
    question: str = Field(..., min_length=1, max_length=5000)
    document_ids: Optional[List[uuid.UUID]] = None
    max_chunks: Optional[int] = Field(5, ge=1, le=20)


class ChatQueryResponse(BaseModel):
    """Chat query response."""
    answer: str
    sources: List[dict]
    model_used: str


# Summarization Schemas

class SummarizationRequest(BaseModel):
    """Summarization request."""
    document_id: uuid.UUID
    use_premium_model: bool = False


class SummarizationResponse(BaseModel):
    """Summarization response."""
    summary: str
    key_points: List[str]
    word_count: int
    model_used: str


# Feedback Schema (Phase 7.6)

class FeedbackSubmission(BaseModel):
    """Beta feedback submission."""
    message: constr(min_length=1, max_length=2000)
    page: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)


# Health Check Schema

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    database: bool
    cache: bool


# Error Response Schema

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    request_id: Optional[str] = None
