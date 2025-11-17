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
