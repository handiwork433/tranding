"""Database helpers for managing trading positions."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, joinedload

from ..db import models
from ..schemas import ClosePositionRequest


def list_active_positions(db: Session) -> list[models.Position]:
    """Return all currently open positions ordered by the most recent."""

    stmt = (
        select(models.Position)
        .options(joinedload(models.Position.symbol), joinedload(models.Position.orders))
        .where(models.Position.status == "open")
        .order_by(models.Position.opened_at.desc())
    )
    return list(db.scalars(stmt).all())


def _calc_realized_pnl(position: models.Position, qty: Decimal, price: Decimal) -> Decimal:
    direction = Decimal("1") if position.side.lower() == "long" else Decimal("-1")
    return (price - position.entry_price) * qty * direction


def close_position(
    db: Session,
    *,
    position_id: int,
    request: ClosePositionRequest,
    partial: bool | None = False,
) -> Optional[models.Position]:
    """Close a position fully or partially and create a fill order record."""

    try:
        position = (
            db.execute(
                select(models.Position)
                .options(joinedload(models.Position.orders), joinedload(models.Position.symbol))
                .where(models.Position.id == position_id)
                .with_for_update()
            )
            .scalars()
            .one()
        )
    except NoResultFound:
        return None

    qty_requested = Decimal(str(request.qty)) if request.qty is not None else position.quantity
    if qty_requested <= 0:
        return position
    if qty_requested > position.quantity:
        qty_requested = position.quantity

    execution_price = Decimal(str(request.price)) if request.price is not None else position.entry_price
    realized = _calc_realized_pnl(position, qty_requested, execution_price)

    order = models.Order(
        position_id=position.id,
        strategy_id=position.strategy_id,
        symbol_id=position.symbol_id,
        type="market" if request.mode == "market" else "limit",
        side="sell" if position.side.lower() == "long" else "buy",
        status="filled",
        quantity=qty_requested,
        filled_quantity=qty_requested,
        price=execution_price,
        average_price=execution_price,
        reduce_only=True,
    )
    db.add(order)

    position.realized_pnl += realized
    position.quantity -= qty_requested
    position.unrealized_pnl = Decimal("0") if position.quantity == 0 else position.unrealized_pnl

    if position.quantity <= 0 or not partial:
        position.status = "closed"
        position.exit_price = execution_price
        position.closed_at = datetime.now(timezone.utc)
        position.quantity = Decimal("0")
        position.unrealized_pnl = Decimal("0")
    else:
        position.status = "open"

    db.commit()
    db.refresh(position)
    return position
