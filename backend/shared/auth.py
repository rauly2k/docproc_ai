"""Firebase authentication utilities."""

from firebase_admin import auth, credentials, initialize_app
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import secretmanager
import json
import os

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
"""Firebase Authentication utilities."""

from fastapi import HTTPException, Header
from typing import Optional
import firebase_admin
from firebase_admin import auth, credentials
import os

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
"""Firebase Authentication utilities."""

import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import firebase_admin
from firebase_admin import credentials, auth
from .config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        if settings.environment == "dev":
            # Local development: use service account file
            cred = credentials.ApplicationDefault()
        else:
            # Production: get credentials from Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{settings.project_id}/secrets/firebase-credentials/versions/latest"
            response = client.access_secret_version(request={"name": name})
            cred_json = json.loads(response.payload.data.decode("UTF-8"))
            cred = credentials.Certificate(cred_json)

        initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        # Already initialized
        pass


# Security scheme
security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Verify Firebase ID token and return user info."""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Authentication token has expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


def get_tenant_id_from_token(token_data: dict) -> str:
    """Extract tenant_id from Firebase token custom claims."""
_firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
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
        else:
            # Use Application Default Credentials in GCP
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred)


async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Firebase ID token from Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Decoded token data with uid, email, and custom claims
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
            # Use Application Default Credentials (for Cloud Run)
            cred = credentials.ApplicationDefault()
            _firebase_app = firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id or settings.gcp_project_id,
            })

        print("Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")
        print("Running without Firebase authentication (development mode)")


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return decoded claims.

    Args:
        token: Firebase ID token (JWT)

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
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


def get_tenant_id_from_token(token_data: dict) -> str:
    """
    Extract tenant_id from decoded token.
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


        Tenant ID as string

    Raises:
        HTTPException: If tenant_id not found in token
    """
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tenant association found. Please contact support."
            detail="No tenant_id found in token. User may not be associated with a tenant."
            detail="No tenant_id found in authentication token"
        )
    return tenant_id


def get_user_role_from_token(token_data: dict) -> str:
    """Extract user role from Firebase token custom claims."""
    return token_data.get("role", "user")
def get_user_id_from_token(token_data: dict) -> str:
    """
    Extract user_id (Firebase UID) from decoded token.
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
        User ID (Firebase UID)
    """
    return token_data.get("uid", "")


def get_user_role_from_token(token_data: dict) -> str:
    """
    Extract user role from decoded token.

    Args:
        token_data: Decoded Firebase token

    Raises:
        HTTPException: If user is not an admin
    """
    role = get_user_role_from_token(token_data)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    Returns:
        User role (default: 'user')
    """
    return token_data.get("role", "user")
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
def create_firebase_user(email: str, password: str, display_name: Optional[str] = None) -> str:
    """
    Create a new Firebase user.

    Args:
        email: User email
        password: User password
        display_name: User display name (optional)

    Returns:
        Firebase user ID (uid)
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
    """
    try:
        return auth.create_custom_token(uid, additional_claims).decode('utf-8')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}"
        )
