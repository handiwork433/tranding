from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status

from ..schemas import ClosePositionRequest, Position

router = APIRouter()

_DEMO_POSITIONS = [
    Position(
        id=1,
        symbol="BTCUSDT",
        side="long",
        qty=0.5,
        entry_price=27000,
        leverage=5,
        opened_at=datetime.utcnow(),
        unrealized_pnl=150.25,
    ),
    Position(
        id=2,
        symbol="ETHUSDT",
        side="short",
        qty=2.0,
        entry_price=1850,
        leverage=3,
        opened_at=datetime.utcnow(),
        unrealized_pnl=-25.8,
    ),
]


@router.get("/active", response_model=List[Position])
def list_active_positions() -> List[Position]:
    return _DEMO_POSITIONS


@router.post("/{position_id}/close", response_model=Position)
def close_position(position_id: int, payload: ClosePositionRequest) -> Position:
    for index, position in enumerate(_DEMO_POSITIONS):
        if position.id == position_id:
            updated = position.copy(update={"unrealized_pnl": 0.0})
            _DEMO_POSITIONS[index] = updated
            return updated
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")


@router.post("/{position_id}/partial-close", response_model=Position)
def partial_close(position_id: int, payload: ClosePositionRequest) -> Position:
    if payload.qty is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity is required for partial close")

    for index, position in enumerate(_DEMO_POSITIONS):
        if position.id == position_id:
            remaining_qty = max(position.qty - payload.qty, 0)
            updated = position.copy(update={"qty": remaining_qty, "unrealized_pnl": position.unrealized_pnl / 2})
            _DEMO_POSITIONS[index] = updated
            return updated
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
