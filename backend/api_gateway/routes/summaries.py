"""Document summarization routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, DocumentSummary, User, OCRResult
from backend.shared.schemas import SummaryRequest, SummaryResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/generate", status_code=202)
async def generate_summary(
    document_id: uuid.UUID,
    request: SummaryRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Trigger summary generation for a document.

    Model preferences:
    - auto: Automatically select best model based on document
    - flash: Fast, cost-effective (Gemini 1.5 Flash)
    - pro: High quality (Gemini 1.5 Pro)

    Summary types:
    - concise: 3-5 bullet points
    - detailed: Comprehensive summary with sections
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get document
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if document has OCR text (required for summarization)
    ocr_result = db.query(OCRResult).filter(
        OCRResult.document_id == document_id
    ).first()

    if not ocr_result and not document.ocr_completed:
        raise HTTPException(
            status_code=400,
            detail="Document must be OCR'd before summarization. Run OCR first."
        )

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "model_preference": request.model_preference,
        "summary_type": request.summary_type,
    }

    pubsub_publisher.publish_summarization(message)

    # Update status
    document.status = "processing"
    document.processing_started_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Summary generation started",
        "document_id": str(document_id),
        "model_preference": request.model_preference,
        "summary_type": request.summary_type,
        "status": "processing"
    }
"""Document summarization endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, DocumentSummary
from shared.schemas import SummarizationRequest, SummaryResponse, JobStatusResponse
from shared.pubsub import publish_summarization_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()


@router.post("/generate", response_model=JobStatusResponse)
async def generate_summary(
    request: SummarizationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Generate document summary (async)."""
    # Get document
    query = db.query(Document).filter(Document.id == request.document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Publish job to Pub/Sub
    message_id = publish_summarization_job(
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        document_id=document.id,
        gcs_path=document.gcs_path,
        model=request.model,
        options={"max_words": request.max_words}
    )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message="Summarization started. Poll /summaries/{document_id} for results."
    )


@router.get("/{document_id}", response_model=SummaryResponse)
async def get_summary(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get generated summary for a document."""
    tenant_id = get_tenant_id_from_token(token_data)

    summary = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document_id,
            DocumentSummary.tenant_id == tenant_id
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return SummaryResponse.from_orm(summary)


@router.get("", response_model=List[SummaryResponse])
async def list_summaries(
    skip: int = 0,
    limit: int = 50,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """List all summaries for tenant."""
    tenant_id = get_tenant_id_from_token(token_data)

    summaries = (
        db.query(DocumentSummary)
        .filter(DocumentSummary.tenant_id == tenant_id)
        .order_by(DocumentSummary.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [SummaryResponse.from_orm(s) for s in summaries]


@router.delete("/{document_id}", status_code=204)
async def delete_summary(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Delete summary for a document."""
    tenant_id = get_tenant_id_from_token(token_data)

    summary = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document_id,
            DocumentSummary.tenant_id == tenant_id
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    db.delete(summary)
    db.commit()
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get document summary."""
    query = db.query(DocumentSummary).filter(DocumentSummary.document_id == document_id)
    query = tenant_filter.filter_query(query, DocumentSummary)
    summary = query.order_by(DocumentSummary.created_at.desc()).first()

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found. Processing may not be complete."
        )

    return summary
