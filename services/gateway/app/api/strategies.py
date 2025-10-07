"""API endpoints for managing trading strategies."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..crud import strategies as strategy_crud
from ..db import models
from ..db.session import get_db
from ..schemas import Strategy, StrategyCreate, StrategyUpdate

router = APIRouter()


@router.get("", response_model=List[Strategy])
def list_strategies(db: Session = Depends(get_db)) -> List[Strategy]:
    """Return all registered strategies."""

    return list(strategy_crud.get_strategies(db))


@router.post("", response_model=Strategy, status_code=status.HTTP_201_CREATED)
def create_strategy(payload: StrategyCreate, db: Session = Depends(get_db)) -> Strategy:
    """Create a new trading strategy."""

    # In the absence of authentication we assign the seeded admin user as the creator.
    creator = db.query(models.User).filter(models.User.email == settings.first_superuser_email).first()
    creator_pk = creator.id if creator else None
    return strategy_crud.create_strategy(db, payload, creator_pk)


@router.put("/{strategy_id}", response_model=Strategy)
def update_strategy(strategy_id: int, payload: StrategyUpdate, db: Session = Depends(get_db)) -> Strategy:
    """Update strategy configuration."""

    db_strategy = strategy_crud.get_strategy(db, strategy_id)
    if not db_strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    return strategy_crud.update_strategy(db, db_strategy, payload)


@router.post("/{strategy_id}/toggle", response_model=Strategy)
def toggle_strategy(strategy_id: int, db: Session = Depends(get_db)) -> Strategy:
    """Enable or disable a strategy."""

    db_strategy = strategy_crud.get_strategy(db, strategy_id)
    if not db_strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    return strategy_crud.toggle_strategy(db, db_strategy)
