from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import signals as signals_crud
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import Signal

router = APIRouter()


@router.get("/latest", response_model=List[Signal])
def latest_signals(
    symbol: str | None = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> List[Signal]:
    records = signals_crud.list_latest_signals(db, symbol=symbol)
    return [Signal.model_validate(record) for record in records]
