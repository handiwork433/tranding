"""Database helpers for the trading engine."""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy.orm import Session

from services.gateway.app.db import SessionLocal


@contextmanager
def session_scope() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive rollback
        session.rollback()
        raise
    finally:
        session.close()
