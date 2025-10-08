"""Dashboard endpoints aggregating basic platform metrics."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> DashboardSummary:
    """Aggregate lightweight operational metrics from the database."""

    # Aggregate realized and unrealized PnL from positions
    realized = (
        db.query(func.coalesce(func.sum(models.Position.realized_pnl), 0)).scalar() or 0
    )
    unrealized = (
        db.query(func.coalesce(func.sum(models.Position.unrealized_pnl), 0)).scalar() or 0
    )
    equity = float(settings.starting_equity + realized + unrealized)

    # Daily and monthly PnL from metrics table
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = start_of_day.replace(day=1)

    pnl_daily = (
        db.query(func.coalesce(func.sum(models.DailyMetric.pnl), 0))
        .filter(models.DailyMetric.date >= start_of_day)
        .scalar()
        or 0
    )
    pnl_monthly = (
        db.query(func.coalesce(func.sum(models.DailyMetric.pnl), 0))
        .filter(models.DailyMetric.date >= start_of_month)
        .scalar()
        or 0
    )

    open_positions = (
        db.query(func.count(models.Position.id)).filter(models.Position.status == "open").scalar() or 0
    )

    alerts: list[str] = []
    if open_positions == 0:
        alerts.append("Нет активных позиций — проверьте статусы стратегий и движка.")

    if db.query(models.Strategy).filter(models.Strategy.enabled.is_(True)).count() == 0:
        alerts.append("Стратегии выключены — включите нужные в разделе стратегий.")

    return DashboardSummary(
        equity=round(equity, 2),
        pnl_daily=round(float(pnl_daily), 2),
        pnl_monthly=round(float(pnl_monthly), 2),
        open_positions=int(open_positions),
        alerts=alerts,
    )
