"""CRUD helpers for managing orders."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, joinedload

from ..db import models


def list_orders(db: Session, limit: int = 100) -> list[models.Order]:
    stmt = (
        select(models.Order)
        .options(joinedload(models.Order.symbol))
        .order_by(models.Order.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def cancel_order(db: Session, order_id: int) -> Optional[models.Order]:
    try:
        order = (
            db.execute(
                select(models.Order)
                .options(joinedload(models.Order.position))
                .where(models.Order.id == order_id)
                .with_for_update()
            )
            .scalars()
            .one()
        )
    except NoResultFound:
        return None

    order.status = "cancelled"
    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order
