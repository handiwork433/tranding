"""CRUD helpers for symbol entities."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import models
from ..schemas import SymbolCreate, SymbolUpdate


def list_symbols(db: Session) -> Sequence[models.Symbol]:
    """Return all tracked symbols ordered alphabetically."""

    stmt = select(models.Symbol).order_by(models.Symbol.symbol.asc())
    return db.scalars(stmt).unique().all()


def get_symbol(db: Session, symbol_id: int) -> models.Symbol | None:
    """Fetch a symbol by identifier."""

    stmt = select(models.Symbol).where(models.Symbol.id == symbol_id)
    return db.scalars(stmt).one_or_none()


def create_symbol(db: Session, payload: SymbolCreate) -> models.Symbol:
    """Create a new tradable symbol entry."""

    symbol = models.Symbol(
        exchange=payload.exchange,
        symbol=payload.symbol,
        base=payload.base,
        quote=payload.quote,
        tick_size=payload.tick_size,
        step_size=payload.step_size,
        min_qty=payload.min_qty,
        status=payload.status,
    )
    db.add(symbol)
    db.commit()
    db.refresh(symbol)
    return symbol


def update_symbol(db: Session, db_symbol: models.Symbol, payload: SymbolUpdate) -> models.Symbol:
    """Update mutable symbol fields."""

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_symbol, field, value)
    db.commit()
    db.refresh(db_symbol)
    return db_symbol
