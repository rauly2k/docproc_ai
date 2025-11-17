"""Document filling endpoints (ID extraction + PDF form filling)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, DocumentFillingResult
from shared.schemas import DocumentFillingRequest, DocumentFillingResponse, JobStatusResponse
from shared.pubsub import publish_document_filling_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()


@router.post("/extract-and-fill", response_model=JobStatusResponse)
async def extract_and_fill(
    request: DocumentFillingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Extract ID data and fill PDF form (async)."""
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
    message_id = publish_document_filling_job(
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        document_id=document.id,
        gcs_path=document.gcs_path,
        template_name=request.template_name
    )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message="Document filling started. Poll /filling/{document_id} for results."
    )


@router.get("/{document_id}", response_model=DocumentFillingResponse)
async def get_filling_result(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get document filling result."""
    query = db.query(DocumentFillingResult).filter(DocumentFillingResult.document_id == document_id)
    query = tenant_filter.filter_query(query, DocumentFillingResult)
    result = query.first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filling result not found. Processing may not be complete."
        )

    return result


@router.get("/templates", response_model=list)
async def list_templates(
    current_user: dict = Depends(get_current_user)
):
    """List available PDF form templates."""
    # TODO: Implement template listing
    return [
        {"name": "romanian_id_form", "description": "Romanian ID Card Form"},
        {"name": "generic_form", "description": "Generic Personal Information Form"}
    ]
