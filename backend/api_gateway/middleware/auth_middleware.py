"""Authentication middleware and dependencies."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.auth import verify_firebase_token
from shared.models import User, Tenant


async def get_current_user_from_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verify Firebase token and get current user info.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Dict containing user info (uid, email, tenant_id, role, db_user_id)

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    # Verify Firebase token
    decoded_token = verify_firebase_token(authorization)

    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")

    # Get user from database
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database. Please complete registration."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Check tenant is active
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive"
        )

    return {
        "firebase_uid": firebase_uid,
        "user_id": str(user.id),
        "email": email,
        "tenant_id": str(user.tenant_id),
        "role": user.role,
        "user": user
    }


async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """
    Get current authenticated user.

    This is an alias for get_current_user_from_token for cleaner dependency injection.
    """
    return current_user


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require user to have admin role.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current user dict

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def get_optional_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if token is provided, otherwise None.

    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not authorization:
        return None

    try:
        return get_current_user_from_token(authorization, db)
    except HTTPException:
        return None
