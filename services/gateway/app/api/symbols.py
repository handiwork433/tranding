"""API endpoints for managing supported trading symbols."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crud import symbols as symbols_crud
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import Symbol, SymbolCreate, SymbolUpdate

router = APIRouter()


@router.get("", response_model=List[Symbol])
def list_symbols(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> List[Symbol]:
    """Return configured symbols."""

    return list(symbols_crud.list_symbols(db))


@router.post("", response_model=Symbol, status_code=status.HTTP_201_CREATED)
def create_symbol(
    payload: SymbolCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("admin",)),
) -> Symbol:
    """Register a new symbol."""

    return symbols_crud.create_symbol(db, payload)


@router.put("/{symbol_id}", response_model=Symbol)
def update_symbol(
    symbol_id: int,
    payload: SymbolUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("admin",)),
) -> Symbol:
    """Update symbol metadata."""

    db_symbol = symbols_crud.get_symbol(db, symbol_id)
    if not db_symbol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not found")
    return symbols_crud.update_symbol(db, db_symbol, payload)
