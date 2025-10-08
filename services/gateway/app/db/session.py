"""Database session and engine configuration."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings


def _sqlite_connect_args(database_url: str) -> dict[str, str]:
    """Return SQLite specific connection arguments."""

    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(settings.database_url, connect_args=_sqlite_connect_args(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Session:
    """Provide a database session dependency for request handling."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
