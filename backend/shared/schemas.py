"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


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


# Document schemas
class DocumentUpload(BaseModel):
    document_type: str = Field(..., pattern="^(invoice|contract|id|generic)$")


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    document_type: str
    status: str
    gcs_path: str
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Summary schemas
class SummaryRequest(BaseModel):
    """Request to generate summary."""
    model_preference: str = Field(default="auto", pattern="^(auto|flash|pro)$")
    summary_type: str = Field(default="concise", pattern="^(concise|detailed)$")


class SummaryResponse(BaseModel):
    """Summary response."""
    id: UUID
    document_id: UUID
    summary: str
    key_points: List[str]
    word_count: int
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True
