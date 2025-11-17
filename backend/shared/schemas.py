"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr


# Base schemas
class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str
    subdomain: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str
    document_type: Optional[str] = None


# Response schemas
class DocumentResponse(BaseModel):
    """Document response schema."""
    id: UUID
    filename: str
    document_type: Optional[str]
    status: str
    gcs_path: str
    gcs_processed_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Document filling schemas
class DocumentFillingRequest(BaseModel):
    """Request to fill document."""
    id_document_id: UUID
    template_name: str


class FillingTemplateInfo(BaseModel):
    """PDF template information."""
    name: str
    display_name: str
    description: str
    fields: List[str]


class FilledDocumentResponse(BaseModel):
    """Filled document response."""
    output_document_id: UUID
    download_url: str
    extracted_data: dict
    template_used: str
    created_at: datetime
