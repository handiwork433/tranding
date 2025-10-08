"""Authentication middleware enforcing bearer token access control."""
from __future__ import annotations

from typing import Iterable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..core.security import AuthenticatedIdentity, decode_token
from ..db import models
from ..db.session import SessionLocal


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate JWT access tokens for protected routes."""

    def __init__(self, app, public_paths: Iterable[str]):
        super().__init__(app)
        self.public_paths = tuple(public_paths)

    def _is_public(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.public_paths)

    async def dispatch(self, request: Request, call_next) -> Response:
        if self._is_public(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                {"detail": "Not authenticated"}, status_code=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token, expected_type="access")
        except Exception:  # broad except ensures sanitized response
            return JSONResponse(
                {"detail": "Invalid authentication credentials"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or role is None:
            return JSONResponse(
                {"detail": "Invalid authentication credentials"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        with SessionLocal() as db:
            user = db.get(models.User, int(user_id))
            if not user or not user.is_active:
                return JSONResponse(
                    {"detail": "Inactive or missing user"}, status_code=status.HTTP_401_UNAUTHORIZED
                )

            request.state.identity = AuthenticatedIdentity(user_id=user.id, role=user.role, email=user.email)

        return await call_next(request)
