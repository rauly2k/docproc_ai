"""Invoice processing routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.shared.database import get_db
from backend.shared.models import Document, InvoiceData, User
from backend.shared.schemas import InvoiceDataResponse, InvoiceValidation
from backend.shared.auth import verify_firebase_token, get_tenant_id_from_token
from backend.shared.pubsub import PubSubPublisher

router = APIRouter()
pubsub_publisher = PubSubPublisher()


@router.post("/{document_id}/process", status_code=202)
async def process_invoice(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Trigger invoice processing for a document.

    Returns 202 Accepted immediately, processing happens async.
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

    if document.document_type != "invoice":
        raise HTTPException(status_code=400, detail="Document is not an invoice")

    # Publish to Pub/Sub
    message = {
        "tenant_id": str(tenant_id),
        "user_id": str(document.user_id),
        "document_id": str(document_id),
        "gcs_path": document.gcs_path,
        "document_type": "invoice",
        "filename": document.filename,
    }

    pubsub_publisher.publish_invoice_processing(message)

    # Update status
    document.status = "processing"
    document.processing_started_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Invoice processing started",
        "document_id": str(document_id),
        "status": "processing"
    }


@router.get("/{document_id}", response_model=InvoiceDataResponse)
async def get_invoice_data(
    document_id: uuid.UUID,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """Get extracted invoice data."""
    tenant_id = get_tenant_id_from_token(token_data)

    invoice_data = (
        db.query(InvoiceData)
        .filter(
            InvoiceData.document_id == document_id,
            InvoiceData.tenant_id == tenant_id
        )
        .first()
    )

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice data not found")

    return InvoiceDataResponse.from_orm(invoice_data)


@router.get("", response_model=List[InvoiceDataResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 50,
    validated_only: bool = False,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """List all invoices for tenant."""
    tenant_id = get_tenant_id_from_token(token_data)

    query = db.query(InvoiceData).filter(InvoiceData.tenant_id == tenant_id)

    if validated_only:
        query = query.filter(InvoiceData.is_validated == True)

    invoices = (
        query
        .order_by(InvoiceData.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [InvoiceDataResponse.from_orm(inv) for inv in invoices]


@router.patch("/{document_id}/validate", response_model=InvoiceDataResponse)
async def validate_invoice(
    document_id: uuid.UUID,
    validation: InvoiceValidation,
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-loop validation/correction of invoice data.

    This is a critical compliance requirement for EU AI Act.
    """
    tenant_id = get_tenant_id_from_token(token_data)

    # Get user
    user = db.query(User).filter(User.firebase_uid == token_data["uid"]).first()

    # Get invoice data
    invoice_data = (
        db.query(InvoiceData)
        .filter(
            InvoiceData.document_id == document_id,
            InvoiceData.tenant_id == tenant_id
        )
        .first()
    )

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Invoice data not found")

    # Apply corrections
    for field, value in validation.corrections.items():
        if hasattr(invoice_data, field):
            setattr(invoice_data, field, value)

    # Mark as validated
    invoice_data.is_validated = True
    invoice_data.validated_by = user.id
    invoice_data.validated_at = datetime.utcnow()
    invoice_data.validation_notes = validation.validation_notes

    db.commit()
    db.refresh(invoice_data)

    return InvoiceDataResponse.from_orm(invoice_data)
