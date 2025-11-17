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
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentUpload(BaseModel):
    """Document upload metadata."""
    document_type: str = Field(..., pattern="^(invoice|contract|id|generic)$")


class DocumentResponse(BaseModel):
    """Document response."""
    id: UUID
    filename: str
    document_type: str
    status: str
    file_size_bytes: Optional[int]
    gcs_path: str
    rag_indexed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    model_used: str
    word_count: int
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
