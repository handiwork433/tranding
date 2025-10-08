"""Application factory for the trading gateway service."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import auth, dashboard, strategies, symbols, positions, orders, signals, reports
from .core.config import settings
from .core.middleware import AuthMiddleware
from .db import Base, SessionLocal, engine
from .db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Ensure database schema exists and seed default records."""

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(title=settings.project_name, version=settings.api_version, lifespan=lifespan)
    app.add_middleware(AuthMiddleware, public_paths=settings.public_paths)

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
    app.include_router(symbols.router, prefix="/symbols", tags=["symbols"])
    app.include_router(positions.router, prefix="/positions", tags=["positions"])
    app.include_router(orders.router, prefix="/orders", tags=["orders"])
    app.include_router(signals.router, prefix="/signals", tags=["signals"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])

    return app


app = create_app()
