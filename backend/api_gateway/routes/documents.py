"""Document management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document
from shared.schemas import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentMetadata,
    SuccessResponse
)
from shared.config import get_settings
from shared.gcs import upload_file_to_gcs, delete_file_from_gcs
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

settings = get_settings()
router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document.

    Args:
        file: Document file
        document_type: Type of document (invoice, contract, id, generic)

    Returns:
        Document upload response with document ID
    """
    # Validate file size
    contents = await file.read()
    file_size = len(contents)
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size_mb} MB"
        )

    # Validate MIME type
    if file.content_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(settings.allowed_mime_types)}"
        )

    # Generate document ID
    document_id = uuid.uuid4()

    # Upload to GCS
    try:
        # Reset file pointer
        await file.seek(0)

        gcs_path = upload_file_to_gcs(
            file_data=file.file,
            tenant_id=current_user["tenant_id"],
            document_id=document_id,
            filename=file.filename,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Create document record in database
    document = Document(
        id=document_id,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        filename=file.filename,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size_bytes=file_size,
        document_type=document_type or "generic",
        gcs_path=gcs_path,
        status="uploaded"
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentUploadResponse(
        document_id=document.id,
        status=document.status,
        filename=document.filename,
        gcs_path=document.gcs_path,
        created_at=document.created_at
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """
    List user's documents with pagination and filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        document_type: Filter by document type
        status: Filter by status

    Returns:
        Paginated list of documents
    """
    # Build query
    query = db.query(Document)
    query = tenant_filter.filter_query(query, Document)
    query = query.filter(Document.user_id == current_user["user_id"])

    # Apply filters
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if status:
        query = query.filter(Document.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()

    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get document by ID."""
    query = db.query(Document).filter(Document.id == document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.patch("/{document_id}/metadata", response_model=DocumentResponse)
async def update_document_metadata(
    document_id: uuid.UUID,
    metadata: DocumentMetadata,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Update document metadata."""
    query = db.query(Document).filter(Document.id == document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update fields
    if metadata.document_type is not None:
        document.document_type = metadata.document_type
    if metadata.filename is not None:
        document.filename = metadata.filename

    db.commit()
    db.refresh(document)

    return document


@router.delete("/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Delete a document."""
    query = db.query(Document).filter(Document.id == document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete from GCS
    try:
        delete_file_from_gcs(document.gcs_path)
        if document.gcs_processed_path:
            delete_file_from_gcs(document.gcs_processed_path)
    except Exception as e:
        print(f"Warning: Failed to delete GCS files: {e}")

    # Delete from database (cascades to related records)
    db.delete(document)
    db.commit()

    return SuccessResponse(
        success=True,
        message="Document deleted successfully"
    )
