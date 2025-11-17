"""Multi-tenancy middleware and utilities."""

from typing import Any, Dict
from fastapi import Depends
from sqlalchemy.orm import Session, Query
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import Tenant
from .auth_middleware import get_current_user


class TenantFilter:
    """
    Helper class to automatically filter queries by tenant_id.

    This ensures multi-tenant data isolation.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def filter_query(self, query: Query, model: Any) -> Query:
        """
        Add tenant_id filter to a query.

        Args:
            query: SQLAlchemy query
            model: SQLAlchemy model class

        Returns:
            Filtered query
        """
        if hasattr(model, 'tenant_id'):
            return query.filter(model.tenant_id == self.tenant_id)
        return query


def get_tenant_filter(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> TenantFilter:
    """
    Get tenant filter for the current user.

    Usage:
        @app.get("/items")
        def get_items(
            db: Session = Depends(get_db),
            tenant_filter: TenantFilter = Depends(get_tenant_filter)
        ):
            query = db.query(Item)
            query = tenant_filter.filter_query(query, Item)
            return query.all()
    """
    return TenantFilter(current_user["tenant_id"])


async def get_current_tenant(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Get the current user's tenant.

    Args:
        current_user: Current user from get_current_user
        db: Database session

    Returns:
        Tenant object
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    return tenant
