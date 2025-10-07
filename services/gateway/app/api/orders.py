from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status

from ..schemas import CancelOrderResponse, Order

router = APIRouter()

_DEMO_ORDERS = [
    Order(
        id=1,
        type="limit",
        side="buy",
        qty=0.2,
        price=26500,
        stop_price=None,
        status="open",
        created_at=datetime.utcnow(),
    ),
    Order(
        id=2,
        type="oco",
        side="sell",
        qty=0.2,
        price=28000,
        stop_price=25500,
        status="working",
        created_at=datetime.utcnow(),
    ),
]


@router.get("", response_model=List[Order])
def list_orders() -> List[Order]:
    return _DEMO_ORDERS


@router.post("/cancel/{order_id}", response_model=CancelOrderResponse)
def cancel_order(order_id: int) -> CancelOrderResponse:
    for index, order in enumerate(_DEMO_ORDERS):
        if order.id == order_id:
            cancelled = order.copy(update={"status": "cancelled"})
            _DEMO_ORDERS[index] = cancelled
            return CancelOrderResponse(id=order_id, status=cancelled.status, cancelled_at=datetime.utcnow())
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
