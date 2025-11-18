"""Admin endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import User, Document, InvoiceData, OCRResult, DocumentSummary, AuditLog
from shared.schemas import TenantStatsResponse, UserRoleUpdateRequest, SuccessResponse
from middleware.auth_middleware import require_admin, get_current_user

router = APIRouter()


@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get tenant usage statistics (admin only)."""
    tenant_id = current_user["tenant_id"]

    # Count documents
    total_documents = db.query(Document).filter(Document.tenant_id == tenant_id).count()

    # Count invoices processed
    total_invoices = db.query(InvoiceData).filter(InvoiceData.tenant_id == tenant_id).count()

    # Count OCR results
    total_ocr = db.query(OCRResult).filter(OCRResult.tenant_id == tenant_id).count()

    # Count summaries generated
    total_summaries = db.query(DocumentSummary).filter(DocumentSummary.tenant_id == tenant_id).count()

    # Count RAG queries from audit logs
    total_rag_queries = db.query(AuditLog).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action == 'rag_query'
    ).count()

    # Calculate storage used
    storage_query = db.query(Document).filter(Document.tenant_id == tenant_id)
    total_storage = sum([doc.file_size_bytes or 0 for doc in storage_query.all()])

    return TenantStatsResponse(
        tenant_id=tenant_id,
        total_documents=total_documents,
        total_invoices_processed=total_invoices,
        total_ocr_processed=total_ocr,
        total_summaries_generated=total_summaries,
        total_rag_queries=total_rag_queries,
        storage_used_bytes=total_storage
    )


@router.get("/users", response_model=list)
async def list_tenant_users(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users in the tenant (admin only)."""
    users = db.query(User).filter(User.tenant_id == current_user["tenant_id"]).all()
    return users


@router.post("/users/{user_id}/role", response_model=SuccessResponse)
async def update_user_role(
    user_id: uuid.UUID,
    request: UserRoleUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)."""
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_user["tenant_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = request.role
    db.commit()

    return SuccessResponse(
        success=True,
        message=f"User role updated to {request.role}"
    )


@router.get("/audit-logs", response_model=list)
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get compliance audit logs (admin only)."""
    offset = (page - 1) * page_size

    logs = db.query(AuditLog).filter(
        AuditLog.tenant_id == current_user["tenant_id"]
    ).order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return logs
