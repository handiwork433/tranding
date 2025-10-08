"""SQLAlchemy models representing core trading domain entities."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class."""


class TimestampMixin:
    """Mixin that adds timestamp columns to track record lifecycle."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(TimestampMixin, Base):
    """User account with role-based access control."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="viewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    otp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)

    strategies: Mapped[list["Strategy"]] = relationship(back_populates="created_by", cascade="all, delete-orphan")


class Symbol(TimestampMixin, Base):
    """Tradable instrument supported by the gateway."""

    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exchange: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    base: Mapped[str] = mapped_column(String(32), nullable=False)
    quote: Mapped[str] = mapped_column(String(32), nullable=False)
    tick_size: Mapped[float] = mapped_column(Float, default=0.01, nullable=False)
    step_size: Mapped[float] = mapped_column(Float, default=0.001, nullable=False)
    min_qty: Mapped[float] = mapped_column(Float, default=0.001, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="trading", nullable=False)

    strategies: Mapped[list["StrategySymbol"]] = relationship(
        back_populates="symbol", cascade="all, delete-orphan"
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="symbol", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="symbol", cascade="all, delete-orphan")
    signals: Mapped[list["Signal"]] = relationship(back_populates="symbol", cascade="all, delete-orphan")


class Strategy(TimestampMixin, Base):
    """Trading strategy configuration and runtime state."""

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="paper", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timeframes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    risk_profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by: Mapped[User | None] = relationship(back_populates="strategies")
    symbol_links: Mapped[list["StrategySymbol"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", passive_deletes=True
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", passive_deletes=True
    )
    orders: Mapped[list["Order"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", passive_deletes=True
    )
    signals: Mapped[list["Signal"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", passive_deletes=True
    )
    daily_metrics: Mapped[list["DailyMetric"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", passive_deletes=True
    )


class StrategySymbol(TimestampMixin, Base):
    """Association table between strategies and tradable symbols."""

    __tablename__ = "strategy_symbols"
    __table_args__ = (UniqueConstraint("strategy_id", "symbol_id", name="uq_strategy_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    timeframes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    risk_profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_position_size_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    strategy: Mapped[Strategy] = relationship(back_populates="symbol_links")
    symbol: Mapped[Symbol] = relationship(back_populates="strategies")


class Position(TimestampMixin, Base):
    """Represents an open or closed trading position."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), default="paper", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    leverage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    trailing_stop: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 12), default=Decimal("0"), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 12), default=Decimal("0"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    strategy: Mapped[Strategy] = relationship(back_populates="positions")
    symbol: Mapped[Symbol] = relationship(back_populates="positions")
    orders: Mapped[list["Order"]] = relationship(
        back_populates="position", cascade="all, delete-orphan", passive_deletes=True
    )


class Order(TimestampMixin, Base):
    """Order lifecycle information for a position."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    client_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    exchange_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 12), nullable=False)
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(28, 12), default=Decimal("0"), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    average_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 12), nullable=True)
    time_in_force: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    position: Mapped[Position] = relationship(back_populates="orders")
    strategy: Mapped[Strategy] = relationship(back_populates="orders")
    symbol: Mapped[Symbol] = relationship(back_populates="orders")


class Signal(TimestampMixin, Base):
    """Signals generated by strategies to drive trading decisions."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    components: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    strategy: Mapped[Strategy] = relationship(back_populates="signals")
    symbol: Mapped[Symbol] = relationship(back_populates="signals")


class DailyMetric(TimestampMixin, Base):
    """Aggregated performance metrics used for reporting and dashboards."""

    __tablename__ = "metrics_daily"
    __table_args__ = (UniqueConstraint("strategy_id", "date", name="uq_metrics_daily"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(28, 12), default=Decimal("0"), nullable=False)
    trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_drawdown: Mapped[Decimal] = mapped_column(Numeric(28, 12), default=Decimal("0"), nullable=False)

    strategy: Mapped[Strategy] = relationship(back_populates="daily_metrics")
