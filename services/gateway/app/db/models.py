"""SQLAlchemy models representing core trading domain entities."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
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

    strategies: Mapped[list["StrategySymbol"]] = relationship(back_populates="symbol", cascade="all, delete-orphan")


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
