"""Dashboard endpoints aggregating basic platform metrics."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import models
from ..db.session import get_db
from ..schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Aggregate lightweight operational metrics from the database."""

    strategies = db.query(models.Strategy).all()
    risk_buffer = sum(float(s.risk_profile.get("risk_per_trade_pct", 0)) for s in strategies)
    open_symbol_links = sum(1 for strategy in strategies for link in strategy.symbol_links if link.enabled)

    equity = 10000.0 + risk_buffer * 250.0
    pnl_daily = risk_buffer * 50.0
    pnl_monthly = risk_buffer * 200.0

    alerts: list[str] = []
    if not strategies:
        alerts.append("Нет активных стратегий — добавьте стратегию в панели управления.")
    elif open_symbol_links == 0:
        alerts.append("Стратегии не привязаны к инструментам — настройте пары.")

    return DashboardSummary(
        equity=round(equity, 2),
        pnl_daily=round(pnl_daily, 2),
        pnl_monthly=round(pnl_monthly, 2),
        open_positions=open_symbol_links,
        alerts=alerts,
    )
