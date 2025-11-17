"""Chat with PDF (RAG) endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Document
from shared.schemas import ChatIndexRequest, ChatQueryRequest, ChatQueryResponse, JobStatusResponse
from shared.pubsub import publish_rag_ingestion_job
from middleware.auth_middleware import get_current_user
from middleware.tenant_middleware import get_tenant_filter, TenantFilter

router = APIRouter()


@router.post("/index", response_model=JobStatusResponse)
async def index_document(
    request: ChatIndexRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """Index document for chat/RAG (async)."""
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
    message_id = publish_rag_ingestion_job(
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
        document_id=document.id,
        gcs_path=document.gcs_path
    )

    return JobStatusResponse(
        job_id=message_id,
        status="processing",
        message="Document indexing started for RAG."
    )


@router.post("/query", response_model=ChatQueryResponse)
async def query_documents(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_filter: TenantFilter = Depends(get_tenant_filter)
):
    """
    Query documents with RAG (Chat with PDF).

    Note: This endpoint would typically call a RAG query worker.
    For now, it returns a placeholder response.
    """
    # Verify documents exist and belong to user's tenant
    for doc_id in request.document_ids:
        query = db.query(Document).filter(Document.id == doc_id)
        query = tenant_filter.filter_query(query, Document)
        document = query.first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )

    # TODO: Implement RAG query logic
    # For now, return placeholder
    return ChatQueryResponse(
        answer="RAG query functionality will be implemented in Phase 5",
        sources=[],
        model_used="gemini-1.5-flash"
    )
