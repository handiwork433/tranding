from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import positions as positions_crud
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import ClosePositionRequest, Position

router = APIRouter()


@router.get("/active", response_model=List[Position])
def list_active_positions(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> List[Position]:
    records = positions_crud.list_active_positions(db)
    return [Position.model_validate(record) for record in records]


@router.post("/{position_id}/close", response_model=Position)
def close_position(
    position_id: int,
    payload: ClosePositionRequest,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("trader", "admin")),
) -> Position:
    position = positions_crud.close_position(db, position_id=position_id, request=payload)
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    return Position.model_validate(position)


@router.post("/{position_id}/partial-close", response_model=Position)
def partial_close(
    position_id: int,
    payload: ClosePositionRequest,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("trader", "admin")),
) -> Position:
    if payload.qty is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity is required for partial close")

    position = positions_crud.close_position(db, position_id=position_id, request=payload, partial=True)
    if not position:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    return Position.model_validate(position)
