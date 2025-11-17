"""Document filling routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend.shared.database import get_db
from backend.shared.models import Document, User
from backend.shared.schemas import DocumentFillingRequest, FillingTemplateInfo, FilledDocumentResponse
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher
from backend.shared.gcs import GCSManager

router = APIRouter()
pubsub_publisher = PubSubPublisher()
gcs_manager = GCSManager()


@router.get("/templates", response_model=List[FillingTemplateInfo])
async def list_templates():
    """List available PDF form templates."""
    # Hardcoded for MVP, could be made dynamic
    templates = [
        FillingTemplateInfo(
            name="romanian_standard_form",
            display_name="Romanian Standard Form",
            description="Standard form for Romanian documents",
            fields=["nume", "prenume", "cnp", "data_nasterii", "adresa"]
        ),
    ]
    return templates


@router.post("/extract-and-fill", status_code=202)
async def extract_and_fill(
    request: DocumentFillingRequest,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Extract data from ID document and fill PDF form.

    Flow:
    1. Validate ID document exists
    2. Create output document record
    3. Publish job to Pub/Sub
    4. Return output document ID
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get ID document
    id_document = db.query(Document).filter(
        Document.id == request.id_document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not id_document:
        raise HTTPException(status_code=404, detail="ID document not found")

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Create output document record
    output_document_id = uuid.uuid4()
    output_document = Document(
        id=output_document_id,
        tenant_id=tenant_id,
        user_id=user.id,
        filename=f"filled_{request.template_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
        document_type="filled_form",
        gcs_path=f"gs://placeholder/{output_document_id}",  # Will be updated by worker
        status="processing",
        processing_started_at=datetime.utcnow()
    )
    db.add(output_document)
    db.commit()

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(user.id),
        "id_document_id": str(request.id_document_id),
        "template_name": request.template_name,
        "output_document_id": str(output_document_id)
    }

    pubsub_publisher.publish_document_filling(message)

    return {
        "message": "Document filling started",
        "output_document_id": str(output_document_id)
    }


@router.get("/{document_id}/download")
async def get_filled_pdf(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get download URL for filled PDF."""
    tenant_id = get_tenant_id_from_token(token_data)

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.gcs_processed_path:
        raise HTTPException(status_code=400, detail="Document not yet processed")

    # Generate signed URL
    download_url = gcs_manager.get_signed_url(
        document.gcs_processed_path,
        expiration_minutes=15
    )

    return {
        "download_url": download_url,
        "expires_in_minutes": 15,
        "filename": document.filename
    }
