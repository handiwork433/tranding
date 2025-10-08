"""Configuration for the trading engine service."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from services.gateway.app.core.config import settings as gateway_settings


class EngineSettings(BaseSettings):
    """Runtime configuration for the trading engine."""

    mode: str = "paper"  # live | paper | backtest
    poll_interval_seconds: int = 60
    database_url: str = gateway_settings.database_url
    starting_equity: float = gateway_settings.starting_equity
    binance_api_key: str | None = None
    binance_api_secret: str | None = None
    binance_use_testnet: bool = True
    binance_futures: bool = True
    binance_base_url: str = "https://api.binance.com"
    binance_futures_base_url: str = "https://fapi.binance.com"
    candles_limit: int = 250
    max_open_positions: int = 25
    risk_buffer_pct: float = 0.2
    default_leverage: int = 5
    trailing_trigger_pct: float = 1.0
    trailing_step_pct: float = 0.5
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="ENGINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> EngineSettings:
    return EngineSettings()


settings = get_settings()
