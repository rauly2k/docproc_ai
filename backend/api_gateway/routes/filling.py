"""Document filling endpoints (ID extraction + PDF form filling)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document, DocumentFillingResult
from shared.schemas import DocumentFillingRequest, DocumentFillingResponse, JobStatusResponse, TemplateListResponse, TemplateInfo
from shared.pubsub import publish_document_filling_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter
from pathlib import Path
import json

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


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    current_user: dict = Depends(get_current_user)
):
    """List available PDF form templates."""
    templates = []

    # Path to templates directory
    templates_dir = Path(__file__).parent.parent.parent / "workers" / "docfill_worker" / "templates"

    if not templates_dir.exists():
        # Return default templates if directory doesn't exist
        return TemplateListResponse(
            templates=[
                TemplateInfo(
                    name="cerere_inscriere_fiscala",
                    display_name="Cerere Înscriere Fiscală",
                    description="Formular pentru înregistrarea fiscală",
                    required_fields=["nume", "prenume", "cnp", "adresa"]
                ),
                TemplateInfo(
                    name="declaratie_590",
                    display_name="Declarație 590",
                    description="Declarație fiscală 590",
                    required_fields=["nume", "cnp", "adresa"]
                )
            ]
        )

    # Scan templates directory for PDF files
    for template_file in templates_dir.glob("*.pdf"):
        template_name = template_file.stem

        # Try to load metadata from companion JSON file
        metadata_file = templates_dir / f"{template_name}.json"

        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)

                templates.append(TemplateInfo(
                    name=template_name,
                    display_name=metadata.get("display_name", template_name.replace("_", " ").title()),
                    description=metadata.get("description", ""),
                    required_fields=metadata.get("required_fields", [])
                ))
            except Exception as e:
                # If metadata loading fails, use defaults
                templates.append(TemplateInfo(
                    name=template_name,
                    display_name=template_name.replace("_", " ").title(),
                    description=f"PDF template: {template_name}",
                    required_fields=[]
                ))
        else:
            # No metadata file, use defaults
            templates.append(TemplateInfo(
                name=template_name,
                display_name=template_name.replace("_", " ").title(),
                description=f"PDF template: {template_name}",
                required_fields=[]
            ))

    return TemplateListResponse(templates=templates)
