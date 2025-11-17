"""Firebase Authentication integration."""

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache

from .config import get_settings
from .database import get_db
from .models import Tenant
from sqlalchemy.orm import Session

settings = get_settings()
security = HTTPBearer()


@lru_cache()
def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Not initialized, so initialize it
        if settings.firebase_credentials_path:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id
            })
        else:
            # Use default credentials in GCP environment
            firebase_admin.initialize_app()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify Firebase ID token.

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    initialize_firebase()

    token = credentials.credentials

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current authenticated user and tenant.

    Args:
        token_data: Decoded Firebase token
        db: Database session

    Returns:
        User data including tenant_id

    Raises:
        HTTPException: If user/tenant not found
    """
    firebase_uid = token_data.get("uid")
    email = token_data.get("email")

    # Get or create tenant
    tenant = db.query(Tenant).filter(Tenant.firebase_uid == firebase_uid).first()

    if not tenant:
        # Auto-create tenant on first login
        tenant = Tenant(
            firebase_uid=firebase_uid,
            email=email,
            name=token_data.get("name", email.split("@")[0])
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return {
        "user_id": firebase_uid,
        "tenant_id": str(tenant.id),
        "email": email,
        "name": tenant.name,
        "subscription_tier": tenant.subscription_tier
    }


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> dict | None:
    """Get current user without raising error if not authenticated."""
    if not credentials:
        return None

    try:
        token_data = await verify_firebase_token(credentials)
        return await get_current_user(token_data, db)
    except HTTPException:
        return None


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require user to be admin."""
    # For MVP, check if user has admin role in Firebase custom claims
    # In production, implement proper role-based access control
    if current_user.get("subscription_tier") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
