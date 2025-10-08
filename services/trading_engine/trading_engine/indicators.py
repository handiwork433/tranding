"""Core indicator calculations used by strategies."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Sequence


def ema(values: Sequence[float], length: int) -> list[float]:
    if length <= 0:
        raise ValueError("EMA length must be positive")
    multiplier = 2 / (length + 1)
    ema_values: list[float] = []
    if not values:
        return ema_values
    ema_values.append(values[0])
    for price in values[1:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def rsi(values: Sequence[float], length: int = 14) -> list[float]:
    if length <= 0:
        raise ValueError("RSI length must be positive")
    gains: deque[float] = deque(maxlen=length)
    losses: deque[float] = deque(maxlen=length)
    rsis: list[float] = [50.0] * len(values)
    for idx in range(1, len(values)):
        delta = values[idx] - values[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
        if len(gains) < length:
            continue
        average_gain = sum(gains) / length
        average_loss = sum(losses) / length
        if average_loss == 0:
            rs = float("inf")
        else:
            rs = average_gain / average_loss
        rsis[idx] = 100 - (100 / (1 + rs))
    return rsis


def atr(highs: Iterable[float], lows: Iterable[float], closes: Iterable[float], length: int = 14) -> float:
    highs_list = list(highs)
    lows_list = list(lows)
    closes_list = list(closes)
    if not highs_list or not lows_list or not closes_list:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(highs_list)):
        true_range = max(
            highs_list[i] - lows_list[i],
            abs(highs_list[i] - closes_list[i - 1]),
            abs(lows_list[i] - closes_list[i - 1]),
        )
        trs.append(true_range)
    if not trs:
        return 0.0
    length = min(length, len(trs))
    return sum(trs[-length:]) / length


@dataclass(slots=True)
class SignalResult:
    side: str  # long | short | flat
    score: float
    entry_price: float
    stop_loss: float
    take_profit: float
