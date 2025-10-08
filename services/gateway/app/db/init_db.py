"""Initialise the database with seed data for development usage."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import get_password_hash
from . import models


def init_db(db: Session) -> None:
    """Seed the database with a default admin user, sample symbols and strategies."""

    admin = db.query(models.User).filter(models.User.email == settings.first_superuser_email).first()
    if not admin:
        admin = models.User(
            email=settings.first_superuser_email,
            hashed_password=get_password_hash(settings.first_superuser_password),
            full_name=settings.first_superuser_full_name,
            role="admin",
        )
        db.add(admin)
        db.flush()

    if db.query(models.Symbol).count() == 0:
        db.add_all(
            [
                models.Symbol(
                    exchange="binance_futures",
                    symbol="BTCUSDT",
                    base="BTC",
                    quote="USDT",
                    tick_size=0.1,
                    step_size=0.001,
                    min_qty=0.001,
                ),
                models.Symbol(
                    exchange="binance_futures",
                    symbol="ETHUSDT",
                    base="ETH",
                    quote="USDT",
                    tick_size=0.05,
                    step_size=0.001,
                    min_qty=0.001,
                ),
            ]
        )
        db.flush()

    if db.query(models.Strategy).count() == 0:
        db.add_all(
            [
                models.Strategy(
                    name="MTF Momentum",
                    mode="paper",
                    enabled=True,
                    params={
                        "entry": {"min_score_long": 0.6, "min_score_short": -0.6},
                        "mtf": {
                            "timeframes": ["1m", "5m", "1h"],
                            "confirm_matrix": {"long": {"require_trend_tf": "1h"}},
                        },
                    },
                    timeframes=["1m", "5m", "1h"],
                    risk_profile={"risk_per_trade_pct": 1.0, "max_daily_drawdown_pct": 5},
                    created_by=admin,
                ),
                models.Strategy(
                    name="ATR Swing",
                    mode="live",
                    enabled=False,
                    params={"atr": {"length": 14, "sl_mul": 1.8}},
                    timeframes=["15m", "4h"],
                    risk_profile={"risk_per_trade_pct": 0.7, "max_concurrent_positions": 3},
                    created_by=admin,
                ),
            ]
        )
        db.flush()

    momentum = (
        db.query(models.Strategy).filter(models.Strategy.name == "MTF Momentum").first()
    )
    swing = db.query(models.Strategy).filter(models.Strategy.name == "ATR Swing").first()
    btc_symbol = db.query(models.Symbol).filter(models.Symbol.symbol == "BTCUSDT").first()
    eth_symbol = db.query(models.Symbol).filter(models.Symbol.symbol == "ETHUSDT").first()

    if momentum and btc_symbol:
        link = (
            db.query(models.StrategySymbol)
            .filter(
                models.StrategySymbol.strategy_id == momentum.id,
                models.StrategySymbol.symbol_id == btc_symbol.id,
            )
            .first()
        )
        if not link:
            db.add(
                models.StrategySymbol(
                    strategy=momentum,
                    symbol=btc_symbol,
                    timeframes=["1m", "5m"],
                    weights={"ema": 0.3, "macd": 0.2},
                    risk_profile={"risk_limit_pct": 2.0},
                )
            )

    if swing and eth_symbol:
        link = (
            db.query(models.StrategySymbol)
            .filter(
                models.StrategySymbol.strategy_id == swing.id,
                models.StrategySymbol.symbol_id == eth_symbol.id,
            )
            .first()
        )
        if not link:
            db.add(
                models.StrategySymbol(
                    strategy=swing,
                    symbol=eth_symbol,
                    timeframes=["15m", "1h"],
                    weights={"atr": 0.4, "ema": 0.2},
                    risk_profile={"risk_limit_pct": 1.5},
                )
            )

    if momentum and btc_symbol and db.query(models.Position).count() == 0:
        position = models.Position(
            strategy=momentum,
            symbol=btc_symbol,
            side="long",
            mode="paper",
            status="open",
            leverage=5,
            quantity=Decimal("0.02"),
            entry_price=Decimal("27000"),
            unrealized_pnl=Decimal("120"),
            realized_pnl=Decimal("0"),
            opened_at=datetime.now(timezone.utc) - timedelta(hours=2),
            stop_loss=Decimal("26500"),
            take_profit=Decimal("28000"),
        )
        db.add(position)
        db.flush()
        db.add(
            models.Order(
                position=position,
                strategy=momentum,
                symbol=btc_symbol,
                type="limit",
                side="buy",
                status="filled",
                quantity=Decimal("0.02"),
                filled_quantity=Decimal("0.02"),
                price=Decimal("27000"),
                average_price=Decimal("27000"),
                time_in_force="GTC",
            )
        )

    if momentum and btc_symbol and db.query(models.Signal).count() == 0:
        db.add(
            models.Signal(
                strategy=momentum,
                symbol=btc_symbol,
                timeframe="5m",
                score=0.74,
                side="long",
                components={"ema": 0.4, "macd": 0.3},
            )
        )

    if momentum and db.query(models.DailyMetric).count() == 0:
        for idx in range(5):
            db.add(
                models.DailyMetric(
                    strategy=momentum,
                    date=datetime.now(timezone.utc) - timedelta(days=idx),
                    pnl=Decimal("150") - Decimal(idx * 20),
                    trades=5 - idx,
                    win_rate=0.55 + idx * 0.02,
                    max_drawdown=Decimal("50") + Decimal(idx * 5),
                )
            )

    db.commit()
