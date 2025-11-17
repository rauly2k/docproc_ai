"""Firebase authentication utilities."""

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials, initialize_app
import firebase_admin
from typing import Optional
import os

# Initialize Firebase Admin SDK
try:
    # Try to use application default credentials
    if not firebase_admin._apps:
        cred = credentials.ApplicationDefault()
        initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization warning: {e}")
    # For local development, you might need to set GOOGLE_APPLICATION_CREDENTIALS


security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Verify Firebase ID token and return decoded token data.

    Args:
        credentials: HTTP Authorization credentials

    Returns:
        Decoded token data containing uid, email, and custom claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Authentication token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


def get_tenant_id_from_token(token_data: dict) -> str:
    """
    Extract tenant_id from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        Tenant ID as string

    Raises:
        HTTPException: If tenant_id not found in token
    """
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tenant_id found in authentication token"
        )
    return tenant_id


def get_user_role_from_token(token_data: dict) -> str:
    """
    Extract user role from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        User role (default: 'user')
    """
    return token_data.get("role", "user")


async def create_firebase_user(email: str, password: str) -> str:
    """
    Create a new Firebase user.

    Args:
        email: User email
        password: User password

    Returns:
        Firebase UID

    Raises:
        HTTPException: If user creation fails
    """
    try:
        user_record = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        return user_record.uid
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


async def set_custom_user_claims(uid: str, claims: dict):
    """
    Set custom claims on Firebase user (for tenant_id, role, etc.).

    Args:
        uid: Firebase user ID
        claims: Dictionary of custom claims
    """
    try:
        auth.set_custom_user_claims(uid, claims)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set custom claims: {str(e)}"
        )
