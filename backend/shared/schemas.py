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
    tenant_name: str


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    role: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Document schemas
class DocumentUpload(BaseModel):
    document_type: str = Field(..., pattern="^(invoice|contract|id|generic)$")


class DocumentResponse(BaseModel):
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
    ocr_completed: bool
    invoice_parsed: bool
    summarized: bool
    rag_indexed: bool

    class Config:
        from_attributes = True


# Invoice schemas
class LineItem(BaseModel):
    description: Optional[str]
    quantity: Optional[int]
    unit_price: Optional[Decimal]
    amount: Optional[Decimal]

    class Config:
        from_attributes = True


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
    line_items: List[LineItem]
    is_validated: bool
    validated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceValidation(BaseModel):
    """Validation/correction data from user."""
    corrections: dict
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
