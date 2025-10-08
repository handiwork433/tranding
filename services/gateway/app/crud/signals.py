"""CRUD helpers for strategy signals."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..db import models


def list_latest_signals(
    db: Session,
    *,
    symbol: Optional[str] = None,
    limit: int = 100,
) -> list[models.Signal]:
    stmt = select(models.Signal).options(joinedload(models.Signal.symbol)).order_by(
        models.Signal.created_at.desc()
    )
    if symbol:
        stmt = stmt.join(models.Signal.symbol).where(models.Symbol.symbol == symbol.upper())
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt))
