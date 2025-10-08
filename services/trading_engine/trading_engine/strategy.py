"""Strategy evaluation logic."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

from .indicators import SignalResult, atr, ema, rsi
from .market_data import Kline
from .types import StrategySymbolContext


@dataclass(slots=True)
class StrategyParameters:
    fast_ema: int = 21
    slow_ema: int = 55
    rsi_length: int = 14
    atr_length: int = 14
    atr_multiplier: float = 1.8
    entry_long_threshold: float = 0.6
    entry_short_threshold: float = -0.6
    exit_threshold: float = 0.1


class MultiTimeframeStrategy:
    """Simple EMA + RSI multi-timeframe confirmation strategy."""

    def __init__(self, context: StrategySymbolContext):
        params = context.strategy.params or {}
        entry_params = params.get("entry", {})
        risk_params = params.get("risk", {})
        indicator_params = params.get("indicators", {})
        self.params = StrategyParameters(
            fast_ema=indicator_params.get("fast_ema", 21),
            slow_ema=indicator_params.get("slow_ema", 55),
            rsi_length=indicator_params.get("rsi_length", 14),
            atr_length=indicator_params.get("atr_length", 14),
            atr_multiplier=risk_params.get("atr_multiplier", 1.8),
            entry_long_threshold=entry_params.get("min_score_long", 0.6),
            entry_short_threshold=entry_params.get("min_score_short", -0.6),
            exit_threshold=entry_params.get("exit_threshold", 0.1),
        )
        self.context = context

    def _score(self, closes: List[float], weights: Dict[str, float]) -> float:
        fast = ema(closes, self.params.fast_ema)
        slow = ema(closes, self.params.slow_ema)
        momentum = rsi(closes, self.params.rsi_length)

        score = 0.0
        if len(fast) >= 2 and len(slow) >= 2:
            if fast[-1] > slow[-1]:
                score += weights.get("trend", 0.3)
            else:
                score -= weights.get("trend", 0.3)
        if momentum[-1] > 60:
            score += weights.get("momentum", 0.2)
        elif momentum[-1] < 40:
            score -= weights.get("momentum", 0.2)
        return score

    def evaluate(self, klines: List[Kline]) -> SignalResult:
        closes = [k.close for k in klines]
        highs = [k.high for k in klines]
        lows = [k.low for k in klines]

        weights = {"trend": 0.3, "momentum": 0.2}
        weights.update(self.context.weights or {})
        score = self._score(closes, weights)

        side = "flat"
        if score >= self.params.entry_long_threshold:
            side = "long"
        elif score <= self.params.entry_short_threshold:
            side = "short"

        last_close = closes[-1]
        average_true_range = atr(highs, lows, closes, self.params.atr_length)
        stop_loss = last_close - self.params.atr_multiplier * average_true_range
        take_profit = last_close + self.params.atr_multiplier * average_true_range

        if side == "short":
            stop_loss = last_close + self.params.atr_multiplier * average_true_range
            take_profit = last_close - self.params.atr_multiplier * average_true_range

        return SignalResult(
            side=side,
            score=score,
            entry_price=last_close,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def should_exit(self, position_side: str, score: float) -> bool:
        if position_side == "long" and score <= self.params.exit_threshold:
            return True
        if position_side == "short" and score >= -self.params.exit_threshold:
            return True
        return False

    def trailing_stop(
        self, entry_price: Decimal, mark_price: Decimal, current_stop: Decimal | None
    ) -> Decimal | None:
        trigger = self.params.atr_multiplier
        if mark_price <= 0:
            return current_stop
        if current_stop is None:
            return current_stop
        if mark_price > entry_price * (1 + trigger / 100):
            return max(current_stop, Decimal(mark_price * (1 - trigger / 200)))
        return current_stop
