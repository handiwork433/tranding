"""Common FastAPI dependencies for authentication and RBAC."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .core.security import AuthenticatedIdentity
from .db import models
from .db.session import get_db


def get_current_identity(request: Request) -> AuthenticatedIdentity:
    identity = getattr(request.state, "identity", None)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return identity


def get_current_user(
    identity: AuthenticatedIdentity = Depends(get_current_identity),
    db: Session = Depends(get_db),
) -> models.User:
    user = db.get(models.User, identity.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def require_roles(*roles: str):
    def _dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _dependency
