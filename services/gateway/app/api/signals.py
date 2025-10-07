from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter

from ..schemas import Signal

router = APIRouter()


@router.get("/latest", response_model=List[Signal])
def latest_signals(symbol: str | None = None) -> List[Signal]:
    now = datetime.utcnow()
    signals = [
        Signal(
            strategy_id=1,
            symbol="BTCUSDT",
            timeframe="5m",
            score=0.72,
            side="long",
            created_at=now - timedelta(minutes=1),
        ),
        Signal(
            strategy_id=2,
            symbol="ETHUSDT",
            timeframe="15m",
            score=-0.65,
            side="short",
            created_at=now - timedelta(minutes=3),
        ),
    ]
    if symbol:
        signals = [signal for signal in signals if signal.symbol == symbol.upper()]
    return signals
