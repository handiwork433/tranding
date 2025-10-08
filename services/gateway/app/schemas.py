"""Pydantic schemas for API requests and responses."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp: Optional[str] = Field(default=None, description="One-time password for users with 2FA enabled")


class TwoFactorVerifyRequest(BaseModel):
    email: EmailStr
    password: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token lifetime in seconds")
    user_id: int
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class DashboardSummary(BaseModel):
    equity: float
    pnl_daily: float
    pnl_monthly: float
    open_positions: int
    alerts: List[str] = Field(default_factory=list)


class SymbolBase(BaseModel):
    symbol: Symbol
    exchange: str
    base: str
    quote: str
    tick_size: float = 0.01
    step_size: float = 0.001
    min_qty: float = 0.001
    status: str = "trading"


class SymbolCreate(SymbolBase):
    pass


class SymbolUpdate(BaseModel):
    tick_size: Optional[float] = None
    step_size: Optional[float] = None
    min_qty: Optional[float] = None
    status: Optional[str] = None


class Symbol(SymbolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategySymbolBase(BaseModel):
    symbol_id: int
    timeframes: List[str] = Field(default_factory=list)
    weights: Dict[str, float] = Field(default_factory=dict)
    risk_profile: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    max_position_size_pct: Optional[Decimal] = None


class StrategySymbolCreate(StrategySymbolBase):
    pass


class StrategySymbolUpdate(BaseModel):
    timeframes: Optional[List[str]] = None
    weights: Optional[Dict[str, float]] = None
    risk_profile: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    max_position_size_pct: Optional[Decimal] = None


class StrategySymbol(StrategySymbolBase):
    id: int
    created_at: datetime
    updated_at: datetime
    symbol: Optional[Symbol] = None

    class Config:
        from_attributes = True


class StrategyBase(BaseModel):
    name: str
    mode: str = Field(default="paper", description="Operating mode: live/paper/backtest")
    enabled: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)
    timeframes: List[str] = Field(default_factory=list)
    risk_profile: Dict[str, Any] = Field(default_factory=dict)


class StrategyCreate(StrategyBase):
    symbol_links: List[StrategySymbolCreate] = Field(default_factory=list)


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    mode: Optional[str] = None
    enabled: Optional[bool] = None
    params: Optional[Dict[str, Any]] = None
    timeframes: Optional[List[str]] = None
    risk_profile: Optional[Dict[str, Any]] = None
    symbol_links: Optional[List[StrategySymbolCreate]] = None


class Strategy(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    symbol_links: List[StrategySymbol] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PositionBase(BaseModel):
    id: int
    strategy_id: int
    symbol_id: int
    symbol: Symbol
    side: str
    mode: str
    status: str
    quantity: Decimal
    entry_price: Decimal
    exit_price: Optional[Decimal] = None
    leverage: Optional[int] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    trailing_stop: Optional[Decimal] = None
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    opened_at: datetime
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class Position(PositionBase):
    orders: List["Order"] = Field(default_factory=list)

    class Config(PositionBase.Config):
        pass


class ClosePositionRequest(BaseModel):
    mode: str = Field("market", description="Close mode: market or limit")
    qty: Optional[float] = Field(None, description="Optional quantity for partial close")
    price: Optional[float] = Field(
        None, description="Execution price override for manual closes or paper trading"
    )


class Order(BaseModel):
    id: int
    position_id: int
    strategy_id: int
    symbol_id: int
    symbol: Symbol
    type: str
    side: str
    status: str
    quantity: Decimal
    filled_quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    time_in_force: Optional[str] = None
    reduce_only: bool = False
    client_order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None
    placed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CancelOrderResponse(BaseModel):
    id: int
    status: str
    cancelled_at: datetime


class Signal(BaseModel):
    id: int
    strategy_id: int
    symbol_id: int
    symbol: Symbol
    timeframe: str
    score: float
    side: str
    components: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class PnLReportRow(BaseModel):
    date: datetime
    pnl: float
    trades: int
    win_rate: float


class PnLReport(BaseModel):
    rows: List[PnLReportRow]
    total_pnl: float
    total_trades: int
    average_win_rate: float
