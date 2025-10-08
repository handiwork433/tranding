"""Dataclasses that describe runtime strategy context."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from services.gateway.app.db import models


@dataclass(slots=True)
class StrategySymbolContext:
    strategy: models.Strategy
    symbol: models.Symbol
    timeframes: List[str]
    weights: Dict[str, float]
    risk_profile: Dict[str, Any]
    mode: str

    @property
    def name(self) -> str:
        return f"{self.strategy.name}::{self.symbol.symbol}"


