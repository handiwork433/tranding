"""Security utilities for password hashing and token management."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Union

from jose import jwt
from passlib.context import CryptContext

from .config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def create_access_token(subject: Union[str, int], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for the given subject."""

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode: Dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that the given plaintext password matches the stored hash."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash and salt the provided password."""

    return pwd_context.hash(password)
