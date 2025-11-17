"""OCR endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, OCRResult
from shared.schemas import OCRExtractRequest, OCRResultResponse, JobStatusResponse
from shared.pubsub import publish_ocr_processing_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()


@router.post("/extract", response_model=JobStatusResponse)
async def extract_text(
    request: OCRExtractRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Extract text from document (async OCR processing)."""
    # Get document
    query = db.query(Document).filter(Document.id == request.document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Update document status
    document.status = "processing"
    document.processing_started_at = datetime.utcnow()
    db.commit()

    # Publish job to Pub/Sub
    message_id = publish_ocr_processing_job(
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        document_id=document.id,
        gcs_path=document.gcs_path,
        ocr_method=request.ocr_method
    )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message="OCR processing started. Poll /ocr/{document_id} for results."
    )


@router.get("/{document_id}", response_model=OCRResultResponse)
async def get_ocr_result(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get OCR extraction result."""
    query = db.query(OCRResult).filter(OCRResult.document_id == document_id)
    query = tenant_filter.filter_query(query, OCRResult)
    ocr_result = query.first()

    if not ocr_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR result not found. Processing may not be complete."
        )

    return ocr_result
