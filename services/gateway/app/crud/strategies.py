"""CRUD helpers for strategy entities."""
from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import models
from ..schemas import StrategyCreate, StrategyUpdate


def get_strategies(db: Session) -> Sequence[models.Strategy]:
    """Return all strategies ordered by creation time."""

    stmt = select(models.Strategy).order_by(models.Strategy.created_at.desc())
    return db.scalars(stmt).unique().all()


def get_strategy(db: Session, strategy_id: int) -> models.Strategy | None:
    """Fetch a single strategy by identifier."""

    stmt = select(models.Strategy).where(models.Strategy.id == strategy_id)
    return db.scalars(stmt).unique().one_or_none()


def create_strategy(db: Session, payload: StrategyCreate, creator_id: int | None) -> models.Strategy:
    """Persist a new strategy with optional symbol links."""

    strategy = models.Strategy(
        name=payload.name,
        mode=payload.mode,
        enabled=payload.enabled,
        params=payload.params,
        timeframes=payload.timeframes,
        risk_profile=payload.risk_profile,
        created_by_id=creator_id,
    )

    for link_payload in payload.symbol_links:
        strategy.symbol_links.append(
            models.StrategySymbol(
                symbol_id=link_payload.symbol_id,
                timeframes=link_payload.timeframes,
                weights=link_payload.weights,
                risk_profile=link_payload.risk_profile,
                enabled=link_payload.enabled,
                max_position_size_pct=link_payload.max_position_size_pct,
            )
        )

    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def update_strategy(db: Session, db_strategy: models.Strategy, payload: StrategyUpdate) -> models.Strategy:
    """Update mutable strategy fields."""

    update_data = payload.model_dump(exclude_unset=True)
    link_payloads = update_data.pop("symbol_links", None)
    for field, value in update_data.items():
        setattr(db_strategy, field, value)
    db.commit()
    db.refresh(db_strategy)
    if link_payloads is not None:
        db_strategy = sync_strategy_symbols(db, db_strategy, link_payloads)
    return db_strategy


def toggle_strategy(db: Session, db_strategy: models.Strategy) -> models.Strategy:
    """Flip strategy enabled flag."""

    db_strategy.enabled = not db_strategy.enabled
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


def sync_strategy_symbols(
    db: Session, db_strategy: models.Strategy, link_payloads: Iterable[dict]
) -> models.Strategy:
    """Replace strategy symbol links with provided payloads."""

    db_strategy.symbol_links.clear()
    for link in link_payloads:
        db_strategy.symbol_links.append(
            models.StrategySymbol(
                symbol_id=link["symbol_id"],
                timeframes=link.get("timeframes", []),
                weights=link.get("weights", {}),
                risk_profile=link.get("risk_profile", {}),
                enabled=link.get("enabled", True),
                max_position_size_pct=link.get("max_position_size_pct"),
            )
        )
    db.commit()
    db.refresh(db_strategy)
    return db_strategy
