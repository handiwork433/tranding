"""Market data ingestion for Binance REST/WebSocket feeds."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import httpx

from .config import settings


@dataclass(slots=True)
class Kline:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class BinanceMarketData:
    """Lightweight Binance REST client for historical candles."""

    def __init__(self) -> None:
        base_url = settings.binance_futures_base_url if settings.binance_futures else settings.binance_base_url
        self._endpoint = "/fapi/v1/klines" if settings.binance_futures else "/api/v3/klines"
        self._client = httpx.AsyncClient(base_url=base_url, timeout=15.0)

    async def get_klines(self, symbol: str, interval: str, limit: int) -> List[Kline]:
        response = await self._client.get(
            self._endpoint,
            params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
        )
        response.raise_for_status()
        klines_raw = response.json()
        klines: List[Kline] = []
        for item in klines_raw:
            open_time = datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc)
            klines.append(
                Kline(
                    open_time=open_time,
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                )
            )
        return klines

    async def close(self) -> None:
        await self._client.aclose()
