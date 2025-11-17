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
