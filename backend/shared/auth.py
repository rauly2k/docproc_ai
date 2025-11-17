"""Firebase Authentication utilities."""

from fastapi import HTTPException, Header
from typing import Optional
import firebase_admin
from firebase_admin import auth, credentials
import os

from .config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
        if settings.firebase_credentials_path and os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            # Use Application Default Credentials in GCP
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred)


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Firebase authentication token.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")

        # Initialize Firebase if not already done
        if _firebase_app is None:
            init_firebase()

        # Verify token
        decoded_token = auth.verify_id_token(token)
        return decoded_token

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")


def get_tenant_id_from_token(token_data: dict) -> str:
    """
    Extract tenant_id from decoded token.

    Args:
        token_data: Decoded Firebase token

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If tenant_id not found in token
    """
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tenant_id found in token. User may not be associated with a tenant."
        )
    return tenant_id


def get_user_id_from_token(token_data: dict) -> str:
    """
    Extract user_id (Firebase UID) from decoded token.

    Args:
        token_data: Decoded Firebase token

    Returns:
        User ID (Firebase UID)
    """
    return token_data.get("uid", "")


def get_user_role_from_token(token_data: dict) -> str:
    """
    Extract user role from decoded token.

    Args:
        token_data: Decoded Firebase token

    Returns:
        User role (default: 'user')
    """
    return token_data.get("role", "user")
