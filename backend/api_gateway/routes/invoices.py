"""Invoice processing endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, InvoiceData
from shared.schemas import (
    InvoiceProcessRequest,
    InvoiceDataResponse,
    InvoiceValidationRequest,
    JobStatusResponse,
    SuccessResponse
)
from shared.pubsub import publish_invoice_processing_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()


@router.post("/process", response_model=JobStatusResponse)
async def process_invoice(
    request: InvoiceProcessRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """
    Process an invoice document (async).

    Publishes a job to Pub/Sub for the invoice worker to process.
    """
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
    document.document_type = "invoice"
    db.commit()

    # Publish job to Pub/Sub
    try:
        message_id = publish_invoice_processing_job(
            tenant_id=current_user["tenant_id"],
            user_id=current_user["user_id"],
            document_id=document.id,
            gcs_path=document.gcs_path
        )
    except Exception as e:
        document.status = "failed"
        document.error_message = f"Failed to publish job: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message="Invoice processing started. Poll /invoices/{document_id} for results.",
        estimated_completion=None
    )


@router.get("/{document_id}", response_model=InvoiceDataResponse)
async def get_invoice_data(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Get extracted invoice data."""
    # Get invoice data
    query = db.query(InvoiceData).filter(InvoiceData.document_id == document_id)
    query = tenant_filter.filter_query(query, InvoiceData)
    invoice_data = query.first()

    if not invoice_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice data not found. Processing may not be complete."
        )

    return invoice_data


@router.patch("/{document_id}/validate", response_model=SuccessResponse)
async def validate_invoice(
    document_id: uuid.UUID,
    request: InvoiceValidationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """
    Human-in-the-loop validation/correction of invoice data.
    """
    # Get invoice data
    query = db.query(InvoiceData).filter(InvoiceData.document_id == document_id)
    query = tenant_filter.filter_query(query, InvoiceData)
    invoice_data = query.first()

    if not invoice_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice data not found"
        )

    # Apply corrections (simplified - in production, you'd want more robust correction logic)
    for field, value in request.corrections.items():
        if hasattr(invoice_data, field):
            setattr(invoice_data, field, value)

    # Mark as validated
    invoice_data.is_validated = request.is_approved
    invoice_data.validated_by = current_user["user_id"]
    invoice_data.validated_at = datetime.utcnow()
    invoice_data.validation_notes = request.validation_notes

    db.commit()

    return SuccessResponse(
        success=True,
        message="Invoice validated successfully"
    )


@router.get("", response_model=list)
async def list_invoices(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """List all invoices for tenant."""
    query = db.query(InvoiceData)
    query = tenant_filter.filter_query(query, InvoiceData)

    offset = (page - 1) * page_size
    invoices = query.order_by(InvoiceData.created_at.desc()).offset(offset).limit(page_size).all()

    return invoices
