from datetime import datetime, timedelta

from fastapi import APIRouter

from ..schemas import PnLReport, PnLReportRow

router = APIRouter()


@router.get("/pnl", response_model=PnLReport)
def get_pnl_report(from_date: datetime | None = None, to_date: datetime | None = None) -> PnLReport:
    base_date = datetime.utcnow()
    rows = [
        PnLReportRow(date=base_date - timedelta(days=idx), pnl=100 - idx * 10, trades=5 - idx, win_rate=0.55 + idx * 0.02)
        for idx in range(3)
    ]
    total_pnl = sum(row.pnl for row in rows)
    total_trades = sum(row.trades for row in rows)
    average_win_rate = sum(row.win_rate for row in rows) / len(rows)

    return PnLReport(rows=rows, total_pnl=total_pnl, total_trades=total_trades, average_win_rate=average_win_rate)
