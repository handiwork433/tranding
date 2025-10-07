"""Initialise the database with seed data for development usage."""
from __future__ import annotations

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
        btc = models.Symbol(
            exchange="binance_futures",
            symbol="BTCUSDT",
            base="BTC",
            quote="USDT",
            tick_size=0.1,
            step_size=0.001,
            min_qty=0.001,
        )
        eth = models.Symbol(
            exchange="binance_futures",
            symbol="ETHUSDT",
            base="ETH",
            quote="USDT",
            tick_size=0.05,
            step_size=0.001,
            min_qty=0.001,
        )
        db.add_all([btc, eth])
        db.flush()

    if db.query(models.Strategy).count() == 0:
        momentum = models.Strategy(
            name="MTF Momentum",
            mode="paper",
            enabled=True,
            params={
                "entry": {"min_score_long": 0.6, "min_score_short": -0.6},
                "mtf": {"timeframes": ["1m", "5m", "1h"], "confirm_matrix": {"long": {"require_trend_tf": "1h"}}},
            },
            timeframes=["1m", "5m", "1h"],
            risk_profile={"risk_per_trade_pct": 1.0, "max_daily_drawdown_pct": 5},
            created_by=admin,
        )
        swing = models.Strategy(
            name="ATR Swing",
            mode="live",
            enabled=False,
            params={"atr": {"length": 14, "sl_mul": 1.8}},
            timeframes=["15m", "4h"],
            risk_profile={"risk_per_trade_pct": 0.7, "max_concurrent_positions": 3},
            created_by=admin,
        )
        db.add_all([momentum, swing])
        db.flush()

        btc_symbol = db.query(models.Symbol).filter(models.Symbol.symbol == "BTCUSDT").first()
        eth_symbol = db.query(models.Symbol).filter(models.Symbol.symbol == "ETHUSDT").first()

        if btc_symbol:
            db.add(
                models.StrategySymbol(
                    strategy=momentum,
                    symbol=btc_symbol,
                    timeframes=["1m", "5m"],
                    weights={"ema": 0.3, "macd": 0.2},
                    risk_profile={"risk_limit_pct": 2.0},
                )
            )
        if eth_symbol:
            db.add(
                models.StrategySymbol(
                    strategy=swing,
                    symbol=eth_symbol,
                    timeframes=["15m", "1h"],
                    weights={"atr": 0.4, "ema": 0.2},
                    risk_profile={"risk_limit_pct": 1.5},
                )
            )

    db.commit()
