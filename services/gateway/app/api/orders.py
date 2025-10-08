from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import orders as orders_crud
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import CancelOrderResponse, Order

router = APIRouter()


@router.get("", response_model=List[Order])
def list_orders(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> List[Order]:
    records = orders_crud.list_orders(db)
    return [Order.model_validate(record) for record in records]


@router.post("/cancel/{order_id}", response_model=CancelOrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("trader", "admin")),
) -> CancelOrderResponse:
    order = orders_crud.cancel_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return CancelOrderResponse(
        id=order.id, status=order.status, cancelled_at=datetime.now(timezone.utc)
    )
