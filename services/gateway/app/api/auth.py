"""Authentication endpoints."""
from __future__ import annotations

from datetime import timedelta

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import create_access_token, create_refresh_token, decode_token, verify_password
from ..db import models
from ..db.session import get_db
from ..schemas import LoginRequest, RefreshRequest, TokenResponse, TwoFactorVerifyRequest

router = APIRouter()


def _issue_tokens(user: models.User) -> TokenResponse:
    access_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_expires = timedelta(minutes=settings.refresh_token_expire_minutes)
    access_token = create_access_token(user.id, user.role, access_expires)
    refresh_token = create_refresh_token(user.id, user.role)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_expires.total_seconds()),
        refresh_expires_in=int(refresh_expires.total_seconds()),
        user_id=user.id,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user credentials and optional OTP."""

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    if user.otp_secret:
        if not payload.otp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP required")
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(payload.otp, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    return _issue_tokens(user)


@router.post("/2fa/verify", response_model=TokenResponse)
def verify_otp(payload: TwoFactorVerifyRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate OTP codes explicitly when clients perform staged authentication flows."""

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.otp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no OTP configured")

    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(payload.otp, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Generate a new access token from a valid refresh token."""

    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError as exc:  # pragma: no cover - jose already normalises errors
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user_id = data.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.get(models.User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return _issue_tokens(user)
