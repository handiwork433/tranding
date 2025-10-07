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
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user_id: int
    role: str


class DashboardSummary(BaseModel):
    equity: float
    pnl_daily: float
    pnl_monthly: float
    open_positions: int
    alerts: List[str] = Field(default_factory=list)


class SymbolBase(BaseModel):
    symbol: str
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


class Position(BaseModel):
    id: int
    symbol: str
    side: str
    qty: float
    entry_price: float
    leverage: Optional[int] = None
    opened_at: datetime
    unrealized_pnl: float


class ClosePositionRequest(BaseModel):
    mode: str = Field("market", description="Close mode: market or limit")
    qty: Optional[float] = Field(None, description="Optional quantity for partial close")


class Order(BaseModel):
    id: int
    type: str
    side: str
    qty: float
    price: Optional[float]
    stop_price: Optional[float]
    status: str
    created_at: datetime


class CancelOrderResponse(BaseModel):
    id: int
    status: str
    cancelled_at: datetime


class Signal(BaseModel):
    strategy_id: int
    symbol: str
    timeframe: str
    score: float
    side: str
    created_at: datetime


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
