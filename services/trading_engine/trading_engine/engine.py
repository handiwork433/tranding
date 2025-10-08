"""Main trading engine orchestration."""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
from typing import List

from .broker import BaseBroker, LiveBroker, PaperBroker
from .config import settings
from .db import session_scope
from .logging import configure_logging
from .market_data import BinanceMarketData
from .repository import TradingRepository
from .strategy import MultiTimeframeStrategy
from .types import StrategySymbolContext


class TradingEngine:
    def __init__(self) -> None:
        configure_logging()
        self.logger = logging.getLogger("trading_engine")
        self.market_data = BinanceMarketData()
        self.broker: BaseBroker = LiveBroker() if settings.mode.lower() == "live" else PaperBroker()

    async def run_forever(self) -> None:
        self.logger.info("Запуск торгового движка в режиме %s", settings.mode)
        try:
            while True:
                await self.run_cycle()
                await asyncio.sleep(settings.poll_interval_seconds)
        finally:  # pragma: no cover - cleanup path
            await self.market_data.close()

    async def run_cycle(self) -> None:
        contexts = self._load_contexts()
        if not contexts:
            self.logger.warning("Нет активных стратегий для обработки")
            return
        await asyncio.gather(*(self._process_context(context) for context in contexts))

    def _load_contexts(self) -> List[StrategySymbolContext]:
        with session_scope() as session:
            repo = TradingRepository(session)
            return repo.load_active_strategy_symbols()

    async def _process_context(self, context: StrategySymbolContext) -> None:
        timeframe = context.timeframes[0] if context.timeframes else "5m"
        try:
            klines = await self.market_data.get_klines(
                context.symbol.symbol, timeframe, settings.candles_limit
            )
        except Exception as exc:  # pragma: no cover - network issues
            self.logger.error("Не удалось получить свечи %s: %s", context.name, exc)
            return
        if len(klines) < 10:
            self.logger.debug("Недостаточно данных для %s", context.name)
            return

        strategy = MultiTimeframeStrategy(context)
        signal = strategy.evaluate(klines)
        mark_price = Decimal(str(klines[-1].close))

        with session_scope() as session:
            repo = TradingRepository(session)
            repo.store_signal(context=context, timeframe=timeframe, signal=signal)
            position = repo.get_open_position(context.strategy.id, context.symbol.id)

            if position:
                position = repo.update_unrealised(position, mark_price)
                if signal.side != position.side and signal.side != "flat":
                    await self._close_position(repo, context, position, mark_price)
                    return
                if strategy.should_exit(position.side, signal.score):
                    await self._close_position(repo, context, position, mark_price)
                    return
                current_stop = position.stop_loss
                new_stop = strategy.trailing_stop(position.entry_price, mark_price, current_stop)
                if new_stop and new_stop != current_stop:
                    position.stop_loss = new_stop
                    self.logger.info(
                        "Трейлинг-стоп обновлён %s -> %s для %s",
                        current_stop,
                        new_stop,
                        context.name,
                    )
                return

            if signal.side == "flat":
                self.logger.debug("Сигнал flat для %s", context.name)
                return
            if not repo.enforce_position_limits():
                self.logger.warning("Лимит позиций достигнут, пропускаем %s", context.name)
                return

            quantity = self._position_size(repo, context, signal)
            if quantity <= Decimal("0"):
                self.logger.debug("Риск менеджмент не позволил открыть %s", context.name)
                return

            order_result = await self.broker.submit_order(
                symbol=context.symbol.symbol,
                side="buy" if signal.side == "long" else "sell",
                quantity=quantity,
                order_type="market",
                price=Decimal(str(signal.entry_price)),
                stop_loss=Decimal(str(signal.stop_loss)),
                take_profit=Decimal(str(signal.take_profit)),
            )
            repo.create_position(
                context=context,
                signal=signal,
                quantity=quantity,
                leverage=self._resolve_leverage(context),
                order_result=order_result,
            )
            self.logger.info(
                "Открыта позиция %s %s qty=%s entry=%s",
                context.name,
                signal.side,
                quantity,
                signal.entry_price,
            )

    async def _close_position(
        self,
        repo: TradingRepository,
        context: StrategySymbolContext,
        position,
        mark_price: Decimal,
    ) -> None:
        order_result = await self.broker.submit_order(
            symbol=context.symbol.symbol,
            side="sell" if position.side == "long" else "buy",
            quantity=position.quantity,
            order_type="market",
            price=mark_price,
            reduce_only=True,
        )
        repo.close_position(position, exit_price=mark_price, order_result=order_result)
        self.logger.info("Позиция закрыта %s по цене %s", context.name, mark_price)

    def _resolve_leverage(self, context: StrategySymbolContext) -> int:
        leverage = context.risk_profile.get("leverage") or context.strategy.risk_profile.get("leverage")
        return int(leverage or settings.default_leverage)

    def _position_size(self, repo: TradingRepository, context: StrategySymbolContext, signal) -> Decimal:
        risk_pct = context.risk_profile.get(
            "risk_per_trade_pct",
            context.strategy.risk_profile.get("risk_per_trade_pct", 1.0),
        )
        risk_pct_dec = Decimal(str(risk_pct))
        equity = Decimal(str(repo.equity()))
        risk_amount = equity * risk_pct_dec / Decimal("100")
        stop_distance = abs(Decimal(str(signal.entry_price)) - Decimal(str(signal.stop_loss)))
        if stop_distance <= 0:
            return Decimal("0")
        quantity = risk_amount / stop_distance
        if settings.binance_futures:
            quantity *= Decimal(str(self._resolve_leverage(context)))
        step = Decimal(str(context.symbol.step_size))
        quantity = self._round_step(quantity, step)
        min_qty = Decimal(str(context.symbol.min_qty))
        if quantity < min_qty:
            return Decimal("0")
        return quantity

    @staticmethod
    def _round_step(value: Decimal, step: Decimal) -> Decimal:
        if step == 0:
            return value
        return (value / step).to_integral_value(rounding=ROUND_DOWN) * step
