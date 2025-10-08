"""Database repository for the trading engine."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from services.gateway.app.db import models

from .broker import OrderResult
from .config import settings
from .indicators import SignalResult
from .types import StrategySymbolContext


class TradingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def load_active_strategy_symbols(self) -> List[StrategySymbolContext]:
        query = (
            self.session.query(models.StrategySymbol)
            .options(
                joinedload(models.StrategySymbol.strategy),
                joinedload(models.StrategySymbol.symbol),
            )
            .filter(
                models.StrategySymbol.enabled.is_(True),
                models.StrategySymbol.strategy.has(models.Strategy.enabled.is_(True)),
                models.StrategySymbol.symbol.has(models.Symbol.status == "trading"),
            )
        )
        contexts: List[StrategySymbolContext] = []
        for link in query.all():
            contexts.append(
                StrategySymbolContext(
                    strategy=link.strategy,
                    symbol=link.symbol,
                    timeframes=link.timeframes or link.strategy.timeframes,
                    weights=link.weights or {},
                    risk_profile=link.risk_profile or link.strategy.risk_profile,
                    mode=link.strategy.mode,
                )
            )
        return contexts

    def get_open_position(self, strategy_id: int, symbol_id: int) -> Optional[models.Position]:
        return (
            self.session.query(models.Position)
            .filter(
                models.Position.strategy_id == strategy_id,
                models.Position.symbol_id == symbol_id,
                models.Position.status == "open",
            )
            .order_by(models.Position.opened_at.desc())
            .first()
        )

    def store_signal(
        self,
        *,
        context: StrategySymbolContext,
        timeframe: str,
        signal: SignalResult,
    ) -> models.Signal:
        db_signal = models.Signal(
            strategy_id=context.strategy.id,
            symbol_id=context.symbol.id,
            timeframe=timeframe,
            score=signal.score,
            side=signal.side,
            components={"weights": context.weights},
        )
        self.session.add(db_signal)
        self.session.flush()
        return db_signal

    def create_position(
        self,
        *,
        context: StrategySymbolContext,
        signal: SignalResult,
        quantity: Decimal,
        leverage: int,
        order_result: OrderResult,
    ) -> models.Position:
        position = models.Position(
            strategy_id=context.strategy.id,
            symbol_id=context.symbol.id,
            side=signal.side,
            mode=context.mode,
            status="open",
            leverage=leverage,
            quantity=quantity,
            entry_price=Decimal(signal.entry_price),
            stop_loss=Decimal(signal.stop_loss),
            take_profit=Decimal(signal.take_profit),
            unrealized_pnl=Decimal("0"),
            realized_pnl=Decimal("0"),
            opened_at=datetime.now(timezone.utc),
        )
        self.session.add(position)
        self.session.flush()
        self._create_order_record(position, order_result, reduce_only=False)
        return position

    def _create_order_record(
        self, position: models.Position, order_result: OrderResult, reduce_only: bool
    ) -> models.Order:
        order = models.Order(
            position_id=position.id,
            strategy_id=position.strategy_id,
            symbol_id=position.symbol_id,
            client_order_id=order_result.client_order_id,
            exchange_order_id=order_result.exchange_order_id,
            type=order_result.order_type,
            side=order_result.side,
            status="filled",
            quantity=order_result.quantity,
            filled_quantity=order_result.quantity,
            price=order_result.price,
            average_price=order_result.price,
            reduce_only=reduce_only,
        )
        self.session.add(order)
        self.session.flush()
        return order

    def update_unrealised(self, position: models.Position, mark_price: float) -> models.Position:
        mark = Decimal(str(mark_price))
        direction = Decimal("1") if position.side == "long" else Decimal("-1")
        entry = position.entry_price
        pnl = (mark - entry) * position.quantity * direction
        position.unrealized_pnl = pnl
        position.updated_at = datetime.now(timezone.utc)
        return position

    def close_position(
        self,
        position: models.Position,
        *,
        exit_price: Decimal,
        order_result: OrderResult,
    ) -> models.Position:
        direction = Decimal("1") if position.side == "long" else Decimal("-1")
        realized = (exit_price - position.entry_price) * position.quantity * direction
        position.realized_pnl += realized
        position.unrealized_pnl = Decimal("0")
        position.exit_price = exit_price
        position.closed_at = datetime.now(timezone.utc)
        position.status = "closed"
        position.quantity = Decimal("0")
        self._create_order_record(position, order_result, reduce_only=True)
        return position

    def enforce_position_limits(self) -> bool:
        open_positions = (
            self.session.query(func.count(models.Position.id))
            .filter(models.Position.status == "open")
            .scalar()
            or 0
        )
        return open_positions < settings.max_open_positions

    def equity(self) -> float:
        realized = (
            self.session.query(func.coalesce(func.sum(models.Position.realized_pnl), 0)).scalar() or 0
        )
        unrealized = (
            self.session.query(func.coalesce(func.sum(models.Position.unrealized_pnl), 0)).scalar() or 0
        )
        return float(settings.starting_equity + realized + unrealized)
