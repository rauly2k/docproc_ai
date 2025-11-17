"""Firebase authentication utilities."""

from firebase_admin import auth, credentials, initialize_app
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import secretmanager
import json
import os

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
    tenant_id = token_data.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tenant association found. Please contact support."
        )
    return tenant_id


def get_user_role_from_token(token_data: dict) -> str:
    """Extract user role from Firebase token custom claims."""
    return token_data.get("role", "user")
