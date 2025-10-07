# Binance Automated Trading Platform Specification

## 1. Goals and Key Objectives
- Implement fully automated trading across Binance Spot and Futures (USDT-M) using API integrations.
- Support sophisticated order handling including OCO, stop-loss, take-profit, trailing stops, partial fills, and pyramiding/DCA options.
- Determine trade entries using multi-timeframe (MTF) confirmations combining indicators, price action patterns, and optional ML models.
- Provide a comprehensive web-based control panel to configure strategies, monitor live trades, and review logs/audit trails.
- Deliver backtesting, forward-testing, and paper-trading capabilities with performance reporting.
- Ensure high reliability through auto-reconnections, exchange-side protective orders, secure key storage, and full auditability.

## 2. Scope
- **Markets:** Binance Spot and/or Binance Futures USDT-M (configurable per deployment).
- **Instruments:** Top-N liquid symbols managed via admin UI.
- **Modes:** Live, Paper, Backtest.
- **Orders:** Market, Limit, Stop-Limit, OCO, TP/SL, Trailing Stop, partial closures, optional pyramiding and DCA.

## 3. Non-Functional Requirements
- **Availability:** ≥ 99.5% with resilient infrastructure.
- **Latency:** Signal-to-order execution within 1–2 seconds (WebSocket market data, REST trading).
- **Scalability:** Manage 100+ simultaneous strategy/symbol combinations.
- **Security:** Encrypt secrets (AES-256), enforce IP allowlists, RBAC, 2FA.
- **Logging & Audit:** Retain detailed logs for at least 90 days.

## 4. Architecture Overview
A modular microservice ecosystem, containerized for deployment (Docker Compose for dev, Kubernetes for prod):

| Module | Responsibilities | Key Tech |
| --- | --- | --- |
| **frontend** | React/Next.js UI with Tailwind/shadcn components for dashboards, forms, analytics | Next.js, Tailwind CSS |
| **gateway/api** | REST+WebSocket APIs, authentication, RBAC, serving data to UI | FastAPI or Node.js (NestJS/Express) |
| **data-ingestor** | Subscribe to Binance WebSocket streams (kline, depth, trades), fallback to REST, publish to Redis | Python/Go, Redis |
| **strategy-engine** | Calculate indicators, patterns, MTF confirmation, risk scoring, signal generation | Python (Pydantic), Pandas, TA-Lib |
| **order-router** | Manage order lifecycle, OCO/TP/SL placement, partial fills, trailing logic, reconciliations | Python/Go, Binance SDK |
| **scheduler** | Housekeeping, report generation, WS reinitialization, cron jobs | Celery/APScheduler |
| **backtester** | Historical simulations, walk-forward optimizations, reporting | Python, NumPy, Pandas |
| **notifier** | Push alerts via Telegram/Email/Discord | Celery workers |
| **storage** | PostgreSQL (primary), Redis (cache/queues), MinIO/S3 (exports) | Managed DBs |
| **metrics** | Prometheus scraping, Grafana dashboards | Prometheus, Grafana |
| **reverse-proxy** | SSL termination, routing | Nginx with Let's Encrypt |

## 5. Signal Logic
### 5.1 Timeframes
- Configurable set (default: 1m, 5m, 15m, 1h, 4h, 1d).
- Entry requires lower timeframe trigger with higher timeframe confirmation or non-conflict.
- MTF confirmation matrices editable via UI (JSON).

### 5.2 Indicators and Patterns
- **Trend:** EMA(20/50/200), SMA(200), SuperTrend, Ichimoku (filter).
- **Momentum:** RSI, StochRSI, MACD (crossovers/divergences).
- **Volatility:** ATR (stops/trailing), Bollinger Bands, Keltner Channels.
- **Volume:** OBV, volume spikes.
- **Candlestick patterns:** Pin Bar, Engulfing, Morning/Evening Star, Three Soldiers/Crows with probability weighting.
- **Price Action:** HH/HL/LH/LL structure, breakout/retest, narrow ranges (NR7).
- **Optional ML:** LightGBM/XGBoost classifier as additional filter.

### 5.3 Signal Aggregation
- Assign weight (-1..+1) per indicator/pattern.
- Aggregate score = weighted sum + MTF confirmation bonuses.
- Entry thresholds (e.g., Long ≥ +0.6, Short ≤ -0.6).
- Anti-spam controls: minimal time between signals, optional news filters.

## 6. Risk & Money Management
- Fixed percentage risk per trade (0.5–2%).
- Position sizing: `size = risk_usdt / (entry - stop)` with exchange constraints and fees; handle leverage for futures.
- **Stop/Take-Profit:**
  - Initial SL via ATR multiples, structure, or levels.
  - TP using R multiples (1R/1.5R/2R/3R) with configurable partial exits (e.g., 30/30/40%).
  - Trailing SL triggered after threshold profit (EMA/ATR/percent-based).
- **Advanced:** optional pyramiding (N add-ons with BE adjustments) and DCA for spot.
- Enforce global limits: max concurrent positions, daily drawdown (DTR), temporal filters.

## 7. Order Handling
- Entry via Limit/Market (configurable) with immediate SL/TP placement (OCO where supported).
- Replace unfilled limits after timeout with market execution or cancellation.
- Support partial exits, trailing activation post TP1, exchange-side stop storage.

## 8. Web Control Panel
### 8.1 Pages
- **Dashboard:** Equity curve, PnL, open positions, daily risk, alerts.
- **Strategies:** CRUD with indicator weights, MTF matrices, enable/disable toggles.
- **Trades:**
  - Active: positions with details and manual controls.
  - History: filters, CSV/XLSX export, signal breakdown.
- **Configurations:** Exchange keys (admin only), modes, fees, slippage, risk limits, schedules.
- **Reports:** Win rate, average R, trade durations, drawdowns, symbol rankings, profitability calendar.
- **Logs & Alerts:** Audit records, system messages, errors.

### 8.2 Roles
- Admin (full access), Trader (strategy/trade management without key viewing), Viewer (read-only).

## 9. Binance Integration
- Official REST & WebSocket APIs with API key permissions limited to trading/reading.
- Encrypted key storage (server-side only).
- Robust error handling (retry with exponential backoff, circuit breaker on repeated failures).
- Periodic reconciliation of positions and orders.

## 10. Testing Modes
- **Backtest:** Historical data (kline + tick where available) with commissions, slippage, spread modeling. Metrics: CAGR, MaxDD, MAR, Sharpe/Sortino, Win rate, Avg R, Profit Factor.
- **Walk-Forward:** Train/validate splits, stability report, Monte Carlo simulations.
- **Paper Trading:** Real-time data, simulated order execution without live orders.

## 11. Monitoring & Notifications
- Prometheus metrics (latency, API errors, fill rates, order frequency, load).
- Alerts via Telegram/Email/Discord for trade events, risk breaches, connectivity issues.
- UI incident log.

## 12. Data Storage Schema (Minimum)
- Tables: `users`, `exchanges`, `api_keys`, `symbols`, `strategies`, `strategy_symbols`, `positions`, `orders`, `signals`, `metrics_daily`, `audit_logs`, `backtests`.
- Store secrets encrypted (AES-256); optional Vault/KMS integration.

## 13. API Endpoints (Sample)
- Auth: `POST /auth/login`, `POST /auth/2fa/verify`.
- Dashboard: `GET /dashboard/summary`.
- Strategies: CRUD endpoints with toggle.
- Symbols: `GET /symbols`, `PUT /strategy-symbols/{id}`.
- Positions: `GET /positions/active`, `POST /positions/{id}/close`, `POST /positions/{id}/partial-close`.
- Orders: `GET /orders`, `POST /orders/cancel/{id}`.
- Signals: `GET /signals/latest?symbol=BTCUSDT`.
- Reports: `GET /reports/pnl?from=...&to=...`.
- WebSocket: `/ws/stream` for live data.

## 14. Configuration Example
```yaml
mode: live
exchange: binance_futures
risk:
  max_daily_drawdown_pct: 5
  risk_per_trade_pct: 1
  max_concurrent_positions: 5
order:
  default_type: limit
  max_slippage_pct: 0.05
  place_sl_tp_immediately: true
  trailing:
    enabled: true
    trigger_profit_pct: 1.0
    trail_by_atr_mul: 1.5
mtf:
  timeframes: [1m, 5m, 15m, 1h, 4h]
  confirm_matrix:
    long:
      require_trend_tf: "1h"
      allow_counter_trend: false
    short:
      require_trend_tf: "1h"
indicators:
  ema:
    lengths: [20, 50, 200]
    weight_trend: 0.3
  rsi:
    length: 14
    oversold: 30
    overbought: 70
    weight: 0.2
  macd:
    fast: 12
    slow: 26
    signal: 9
    weight: 0.2
  atr:
    length: 14
    sl_mul: 1.8
patterns:
  engulfing:
    weight: 0.1
  pinbar:
    weight: 0.1
entry:
  min_score_long: 0.6
  min_score_short: -0.6
take_profit:
  r_targets: [1.0, 1.5, 2.0]
  partials: [0.3, 0.3, 0.4]
```

## 15. Position Sizing Example (Futures Long)
- Capital: 10,000 USDT; risk 1% → 100 USDT risk.
- Entry: 100.00; Stop: 98.50 → risk per unit 1.50.
- Position size: 100 / 1.50 = 66.66 ≈ 66 contracts (pre-leverage).
- With 5x leverage: notional up to 330.
- Validate against `minQty`, `stepSize`, fees, margin; round per exchange rules.

## 16. Error Handling & Edge Cases
- WebSocket loss → auto resubscribe, fallback to REST, alert via Telegram.
- Order rejections (LOT_SIZE, PRICE_FILTER, INSUFFICIENT_BALANCE) → degrade gracefully (resize, recalc) and log/alert.
- Time synchronization via exchange server time.
- Deduplicate signals by `clientOrderId`.
- On service restart, restore active states from DB and reattach watchers.

## 17. Security
- Secrets stored in `.env` (server) with optional KMS/Vault.
- Database encryption for API keys (AES-256).
- Strong password policies, 2FA, short-lived sessions, refresh tokens.
- CORS, rate-limits, CSRF protection.
- RBAC enforcement and full auditing.

## 18. Deployment & Infrastructure
- Containerized services orchestrated via Docker Compose (dev) and Kubernetes (prod).
- Supporting services: frontend, api, strategy-engine, order-router, data-ingestor, backtester, notifier, postgres, redis, prometheus, grafana, nginx.
- JSON structured logs aggregated centrally (Loki/ELK).
- CI/CD pipeline: linting, tests, security scans, DB migrations (Alembic/Prisma), automated deploy to staging/prod.

## 19. Testing & Acceptance
- Unit tests for indicators, signal aggregation.
- Integration tests for order flows (Binance sandbox/testnet).
- Load tests: 100 WS subscriptions, latency < 2s.
- Business acceptance:
  - Correct OCO/SL/TP placement and partial exits.
  - Trailing stops trigger as expected.
  - PnL reconciliation with exchange (within fee tolerance).
  - Deterministic backtests (seeded).
  - UI strategy editing, history view, export functions.

## 20. Optional Extensions
- News/event calendar filters for volatility.
- Portfolio-level risk allocation (sector/cluster based).
- Auto strategy generator (AutoML/parameter optimizer).
- Webhooks for external signal ingestion (e.g., TradingView).
