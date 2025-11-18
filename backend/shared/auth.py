"""Firebase Authentication utilities."""

import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import firebase_admin
from firebase_admin import credentials, auth

from .config import get_settings

settings = get_settings()

# Global Firebase app instance
_firebase_app = None


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_app

    if _firebase_app is not None:
        return

    try:
        # Try to use service account credentials if provided
        if settings.firebase_credentials_path and os.path.exists(settings.firebase_credentials_path):
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized with service account")
        else:
            # Use Application Default Credentials (for Cloud Run)
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id or settings.project_id,
            })
            print("✅ Firebase initialized with Application Default Credentials")
    except Exception as e:
        print(f"⚠️  Warning: Firebase initialization failed: {e}")
        print("Running without Firebase authentication (development mode)")


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return decoded claims.

    Args:
        token: Firebase ID token (JWT), may include 'Bearer ' prefix

    Returns:
        Decoded token containing uid, email, and custom claims

    Raises:
        HTTPException: If token is invalid
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided"
        )

    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # Initialize Firebase if not already done
        if _firebase_app is None:
            initialize_firebase()

        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant_id found in authentication token"
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
    Extract user role from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        User role (default: 'user')
    """
    return token_data.get("role", "user")


async def require_admin(token_data: dict) -> None:
    """
    Require admin role for endpoint access.

    Args:
        token_data: Decoded Firebase token

    Raises:
        HTTPException: If user is not an admin
    """
    role = get_user_role_from_token(token_data)
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


async def create_firebase_user(email: str, password: str, display_name: Optional[str] = None) -> str:
    """
    Create a new Firebase user.

    Args:
        email: User email
        password: User password
        display_name: User display name (optional)

    Returns:
        Firebase user ID (uid)

    Raises:
        HTTPException: If user creation fails
    """
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )
        return user.uid
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


def set_custom_user_claims(uid: str, claims: Dict[str, Any]) -> None:
    """
    Set custom claims for a Firebase user (tenant_id, role, etc.).

    Args:
        uid: Firebase user ID
        claims: Custom claims dict (e.g., {'tenant_id': 'xxx', 'role': 'admin'})

    Raises:
        HTTPException: If setting claims fails
    """
    try:
        auth.set_custom_user_claims(uid, claims)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set custom claims: {str(e)}"
        )


def get_user_by_email(email: str) -> Optional[auth.UserRecord]:
    """
    Get Firebase user by email.

    Args:
        email: User email

    Returns:
        UserRecord or None if not found
    """
    try:
        return auth.get_user_by_email(email)
    except auth.UserNotFoundError:
        return None
    except Exception:
        return None


def delete_firebase_user(uid: str) -> None:
    """
    Delete a Firebase user.

    Args:
        uid: Firebase user ID

    Raises:
        HTTPException: If deletion fails
    """
    try:
        auth.delete_user(uid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


def generate_custom_token(uid: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a custom Firebase token for a user.

    Args:
        uid: Firebase user ID
        additional_claims: Additional claims to include in token

    Returns:
        Custom token string

    Raises:
        HTTPException: If token generation fails
    """
    try:
        return auth.create_custom_token(uid, additional_claims).decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}"
        )
