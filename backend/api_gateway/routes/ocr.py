"""OCR routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from backend.shared.database import get_db
from backend.shared.models import Document, OCRResult
from backend.shared.schemas import DocumentResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/extract", status_code=202)
async def extract_text(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Trigger OCR extraction for document."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(document.user_id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "document_type": document.document_type,
        "filename": document.filename,
    }

    pubsub_publisher.publish_ocr_processing(message)

    return {"message": "OCR extraction started", "document_id": str(document_id)}


@router.get("/{document_id}")
async def get_ocr_result(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get OCR extraction result."""
    tenant_id = get_tenant_id_from_token(token_data)

    ocr_result = db.query(OCRResult).filter(
        OCRResult.document_id == document_id,
        OCRResult.tenant_id == tenant_id
    ).first()

    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR result not found")

    return {
        "id": str(ocr_result.id),
        "document_id": str(ocr_result.document_id),
        "extracted_text": ocr_result.extracted_text,
        "confidence_score": float(ocr_result.confidence_score) if ocr_result.confidence_score else None,
        "page_count": ocr_result.page_count,
        "ocr_method": ocr_result.ocr_method,
        "created_at": ocr_result.created_at.isoformat(),
    }
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
