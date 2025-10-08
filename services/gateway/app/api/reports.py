from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import metrics as metrics_crud
from ..dependencies import require_roles
from ..db import models
from ..db.session import get_db
from ..schemas import PnLReport, PnLReportRow

router = APIRouter()


@router.get("/pnl", response_model=PnLReport)
def get_pnl_report(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("viewer", "trader", "admin")),
) -> PnLReport:
    now = datetime.utcnow()
    to_boundary = to_date or now
    from_boundary = from_date or (to_boundary - timedelta(days=30))

    metrics = metrics_crud.get_metrics_range(db, from_date=from_boundary, to_date=to_boundary)
    summary = metrics_crud.summarise_metrics(metrics)

    rows = [
        PnLReportRow(
            date=metric.date,
            pnl=float(metric.pnl),
            trades=metric.trades,
            win_rate=metric.win_rate,
        )
        for metric in metrics
    ]

    return PnLReport(
        rows=rows,
        total_pnl=summary["pnl"],
        total_trades=summary["trades"],
        average_win_rate=summary["win_rate"],
    )
