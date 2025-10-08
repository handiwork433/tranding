"""Security utilities for password hashing and token management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


@dataclass(slots=True)
class AuthenticatedIdentity:
    """Lightweight identity object stored in request state after auth."""

    user_id: int
    role: str
    email: str


def _create_token(
    subject: Union[str, int],
    expires_delta: timedelta,
    token_type: str,
    additional_claims: Mapping[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": token_type,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(subject: Union[str, int], role: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for the given subject."""

    lifetime = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject, lifetime, "access", {"role": role})


def create_refresh_token(subject: Union[str, int], role: str) -> str:
    """Issue a refresh token for the authenticated subject."""

    lifetime = timedelta(minutes=settings.refresh_token_expire_minutes)
    return _create_token(subject, lifetime, "refresh", {"role": role})


def decode_token(token: str, expected_type: str | None = None) -> Dict[str, Any]:
    """Decode and validate a JWT token, optionally checking the token type."""

    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise JWTError(f"Invalid token type: {token_type}")
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the given plaintext password matches the stored hash."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash and salt the provided password."""

    return pwd_context.hash(password)
