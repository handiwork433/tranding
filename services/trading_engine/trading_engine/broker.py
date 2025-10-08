"""Execution layer abstraction for paper and live trading."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException

from .config import settings


@dataclass(slots=True)
class OrderResult:
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    client_order_id: Optional[str] = None
    exchange_order_id: Optional[str] = None


class BaseBroker:
    async def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str,
        price: Decimal,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        reduce_only: bool = False,
    ) -> OrderResult:
        raise NotImplementedError


class PaperBroker(BaseBroker):
    async def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str,
        price: Decimal,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        reduce_only: bool = False,
    ) -> OrderResult:
        return OrderResult(
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )


class LiveBroker(BaseBroker):
    def __init__(self) -> None:
        if not settings.binance_api_key or not settings.binance_api_secret:
            raise ValueError("API ключи Binance не заданы для live-режима")
        self.client = Client(settings.binance_api_key, settings.binance_api_secret)
        if settings.binance_use_testnet:
            self.client.API_URL = "https://testnet.binancefuture.com" if settings.binance_futures else "https://testnet.binance.vision"

    async def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str,
        price: Decimal,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        reduce_only: bool = False,
    ) -> OrderResult:
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": float(quantity),
        }
        if order_type.lower() == "limit":
            params["price"] = float(price)
            params["timeInForce"] = "GTC"
        if settings.binance_futures:
            params["reduceOnly"] = reduce_only
        try:
            response = self.client.create_order(**params)
        except BinanceAPIException as exc:  # pragma: no cover - network side effects
            raise RuntimeError(f"Binance order error: {exc}") from exc

        return OrderResult(
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            client_order_id=response.get("clientOrderId"),
            exchange_order_id=response.get("orderId"),
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
