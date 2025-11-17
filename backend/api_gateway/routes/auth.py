"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.database import get_db
from shared.models import User, Tenant
from shared.schemas import UserSignupRequest, UserResponse, SuccessResponse
from shared.auth import create_firebase_user, set_custom_user_claims, get_user_by_email
from middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: UserSignupRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user account.

    This endpoint:
    1. Creates a Firebase user
    2. Creates or uses existing tenant
    3. Creates user record in database
    4. Sets custom claims on Firebase user
    """
    # Check if user already exists in our database
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Create Firebase user
    firebase_uid = create_firebase_user(
        email=request.email,
        password=request.password,
        display_name=request.full_name
    )

    # Create or get tenant
    tenant = None
    if request.tenant_name:
        # Create new tenant
        tenant = Tenant(
            name=request.tenant_name,
            subdomain=None,  # Can be set later
            is_active=True
        )
        db.add(tenant)
        db.flush()  # Get tenant.id without committing
    else:
        # For MVP, create a default tenant for each user
        # In production, you might want different logic
        tenant = Tenant(
            name=f"{request.full_name or request.email}'s Organization",
            is_active=True
        )
        db.add(tenant)
        db.flush()

    # Create user in database
    user = User(
        firebase_uid=firebase_uid,
        tenant_id=tenant.id,
        email=request.email,
        full_name=request.full_name,
        role="admin",  # First user is admin
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Set custom claims on Firebase user
    set_custom_user_claims(firebase_uid, {
        "tenant_id": str(tenant.id),
        "role": user.role
    })

    return user


@router.post("/login", response_model=SuccessResponse)
async def login(db: Session = Depends(get_db)):
    """
    Login endpoint (handled by Firebase on client side).

    This endpoint is here for documentation purposes.
    Actual authentication is done via Firebase SDK on the client side.

    The client should:
    1. Call Firebase signInWithEmailAndPassword()
    2. Get ID token from Firebase
    3. Use that token in Authorization header for subsequent requests
    """
    return {
        "success": True,
        "message": "Login is handled by Firebase SDK on client side"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return current_user["user"]


@router.post("/logout", response_model=SuccessResponse)
async def logout():
    """
    Logout endpoint (handled by Firebase on client side).

    The client should call Firebase signOut() method.
    """
    return {
        "success": True,
        "message": "Logout is handled by Firebase SDK on client side"
    }
