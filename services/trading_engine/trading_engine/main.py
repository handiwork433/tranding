"""CLI entry point for the trading engine."""
from __future__ import annotations

import asyncio

from .engine import TradingEngine


def run() -> None:
    engine = TradingEngine()
    asyncio.run(engine.run_forever())


if __name__ == "__main__":
    run()
