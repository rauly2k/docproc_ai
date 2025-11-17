"""Firebase authentication utilities."""

import os
from fastapi import HTTPException, Header
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth


# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        # Try to use Application Default Credentials first
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception:
            # Fallback to service account key if available
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                # For development, we can skip Firebase init
                print("Warning: Firebase not initialized. Auth will not work.")


# Initialize on module import
try:
    initialize_firebase()
except Exception as e:
    print(f"Warning: Failed to initialize Firebase: {e}")


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Firebase ID token from Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Decoded token data with uid, email, and custom claims

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")

    try:
        # Verify token with Firebase
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Expired authentication token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def get_tenant_id_from_token(token_data: dict) -> str:
    """
    Extract tenant_id from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        Tenant ID string

    Raises:
        HTTPException: If tenant_id is missing
    """
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="User has no tenant association")

    return tenant_id


def get_user_role_from_token(token_data: dict) -> str:
    """
    Extract user role from Firebase token custom claims.

    Args:
        token_data: Decoded Firebase token

    Returns:
        User role ('admin', 'user', or 'viewer')
    """
    return token_data.get("role", "user")


async def require_admin(token_data: dict):
    """
    Require admin role for endpoint access.

    Args:
        token_data: Decoded Firebase token

    Raises:
        HTTPException: If user is not an admin
    """
    role = get_user_role_from_token(token_data)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
