from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.rate_limiter import login_rate_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    revoke_token,
    verify_password,
)
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import (
    LoginRequest,
    Token,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(
    request: Request,
    login_req: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    POST /auth/login (email + password)
    Returns: access token (15 min) + refresh token (7 days).
    Rate-limited to 5 attempts per minute per IP.
    """
    # 1. Enforce rate limit (5 attempts/min/IP)
    login_rate_limiter.check_rate_limit(request)

    # 2. Authenticate user
    user = db.query(User).filter(User.email == login_req.email).first()
    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # 3. Generate tokens
    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        school_id=user.school_id,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        role=user.role,
        school_id=user.school_id,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=900,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(
    req: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    POST /auth/refresh
    Exchanges a valid 7-day refresh token for a new 15-minute access token and new refresh token.
    """
    payload = decode_access_token(req.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Rotate tokens: revoke the used refresh token
    revoke_token(req.refresh_token)

    new_access_token = create_access_token(
        subject=user.id,
        role=user.role,
        school_id=user.school_id,
    )
    new_refresh_token = create_refresh_token(
        subject=user.id,
        role=user.role,
        school_id=user.school_id,
    )

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=900,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    req: Optional[LogoutRequest] = None,
    authorization: Optional[str] = Header(None),
):
    """
    POST /auth/logout
    Invalidates access and/or refresh token.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        revoke_token(token)

    if req and req.refresh_token:
        revoke_token(req.refresh_token)

    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    GET /auth/me
    Returns current authenticated user profile.
    """
    return UserResponse.model_validate(current_user)
