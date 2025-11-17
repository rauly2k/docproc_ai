"""Firebase authentication utilities."""

import os
from typing import Optional
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import auth, credentials


# Initialize Firebase Admin SDK (only once)
def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Not initialized, initialize now
        # In production, use service account credentials
        # In development, use default credentials
        if os.getenv("FIREBASE_CREDENTIALS_PATH"):
            cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
            firebase_admin.initialize_app(cred)
        else:
            # Use application default credentials
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)


def verify_firebase_token(authorization: str = Header(...)) -> dict:
    """
    Verify Firebase ID token from Authorization header.

    Args:
        authorization: Bearer token from header

    Returns:
        Decoded token with user info

    Raises:
        HTTPException: If token is invalid
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")


def get_tenant_id_from_token(token_data: dict) -> str:
    """
    Extract tenant_id from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        Tenant ID

    Raises:
        HTTPException: If tenant_id not found
    """
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="No tenant association found")
    return tenant_id


def get_user_id_from_token(token_data: dict) -> str:
    """Extract user ID from token."""
    return token_data.get("uid")
