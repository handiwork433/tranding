"""CRUD helpers for performance metrics and reporting."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import models


def get_metrics_range(
    db: Session,
    *,
    from_date: datetime,
    to_date: datetime,
) -> list[models.DailyMetric]:
    stmt = (
        select(models.DailyMetric)
        .where(models.DailyMetric.date >= from_date, models.DailyMetric.date <= to_date)
        .order_by(models.DailyMetric.date.asc())
    )
    return list(db.scalars(stmt))


def summarise_metrics(metrics: Iterable[models.DailyMetric]) -> dict[str, float]:
    metrics_list = list(metrics)
    if not metrics_list:
        return {"pnl": 0.0, "trades": 0, "win_rate": 0.0}

    total_pnl = sum(float(metric.pnl) for metric in metrics_list)
    total_trades = sum(metric.trades for metric in metrics_list)
    average_win_rate = (
        sum(metric.win_rate for metric in metrics_list) / len(metrics_list) if metrics_list else 0.0
    )
    return {"pnl": total_pnl, "trades": total_trades, "win_rate": average_win_rate}
