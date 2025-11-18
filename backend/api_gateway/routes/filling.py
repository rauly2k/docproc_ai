"""Document filling endpoints (ID extraction + PDF form filling)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, DocumentFillingResult, User
from shared.schemas import DocumentFillingRequest, DocumentFillingResponse, JobStatusResponse
from shared.pubsub import publish_document_filling_job
from shared.gcs import GCSManager
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()
gcs_manager = GCSManager()


@router.post("/extract-and-fill", response_model=JobStatusResponse)
async def extract_and_fill(
    request: DocumentFillingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """
    Extract ID data and fill PDF form (async).

    This endpoint creates a new document record for the filled PDF
    and starts async processing.
    """
    # Get ID document
    query = db.query(Document).filter(Document.id == request.document_id)
    query = tenant_filter.filter_query(query, Document)
    id_document = query.first()

    if not id_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ID document not found"
        )

    # Get user for creating output document
    user = db.query(User).filter(User.firebase_uid == current_user["uid"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create output document record for the filled PDF
    output_document_id = uuid.uuid4()
    output_document = Document(
        id=output_document_id,
        tenant_id=current_user["tenant_id"],
        user_id=user.id,
        filename=f"filled_{request.template_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
        document_type="filled_form",
        gcs_path=f"gs://placeholder/{output_document_id}",  # Will be updated by worker
        status="processing",
        processing_started_at=datetime.utcnow()
    )
    db.add(output_document)
    db.commit()

    # Publish job to Pub/Sub
    message = {
        "tenant_id": str(current_user["tenant_id"]),
        "user_id": str(user.id),
        "id_document_id": str(request.document_id),
        "template_name": request.template_name,
        "output_document_id": str(output_document_id)
    }

    message_id = publish_document_filling_job(
        tenant_id=str(current_user["tenant_id"]),
        user_id=str(user.id),
        document_id=request.document_id,
        gcs_path=id_document.gcs_path,
        template_name=request.template_name,
        options={"output_document_id": str(output_document_id)}
    )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message=f"Document filling started. Output document ID: {output_document_id}"
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


@router.get("/templates")
async def list_templates(
    current_user: dict = Depends(get_current_user)
):
    """List available PDF form templates."""
    return [
        {
            "name": "romanian_standard_form",
            "display_name": "Romanian Standard Form",
            "description": "Standard form for Romanian documents",
            "fields": ["nume", "prenume", "cnp", "data_nasterii", "locul_nasterii", "adresa", "seria_ci", "numar_ci"]
        }
    ]


@router.get("/{document_id}/download")
async def get_filled_pdf_download(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get download URL for filled PDF."""
    # Get document
    query = db.query(Document).filter(Document.id == document_id)
    query = tenant_filter.filter_query(query, Document)
    document = query.first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not document.gcs_processed_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document not yet processed. Check status first."
        )

    # Generate signed URL for download (15 minute expiry)
    try:
        download_url = gcs_manager.get_signed_url(
            document.gcs_processed_path,
            expiration_minutes=15
        )

        return {
            "download_url": download_url,
            "expires_in_minutes": 15,
            "filename": document.filename,
            "file_size_bytes": document.file_size_bytes
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating download URL: {str(e)}"
        )
