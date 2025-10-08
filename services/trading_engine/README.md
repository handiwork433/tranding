# Trading Engine

Асинхронный движок, который подключается к базе шлюза, генерирует торговые сигналы и исполняет их через бумажного брокера или напрямую на Binance.

## Возможности

- Чтение стратегий и инструментов из базы данных шлюза.
- Получение свечей с Binance (spot или USDT-M futures, настраивается через `.env`).
- Расчёт MTF-сигнала на основе EMA/RSI/ATR.
- Управление размером позиции согласно риск-профилю стратегии и настройкам инструмента.
- Ведение сигналов, ордеров и позиций в общей БД.
- Поддержка paper/live режимов, трейлинг-стопов и частичного закрытия по стопам.

## Быстрый старт

```bash
cd services/trading_engine
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
# отредактируйте ключи Binance и путь к БД при необходимости
trading-engine
```

По умолчанию движок запускается в paper-режиме и использует ту же SQLite/PostgreSQL базу, что и шлюз (`GATEWAY_DATABASE_URL`).

Для боевого режима укажите `ENGINE_MODE=live` и заполните `ENGINE_BINANCE_API_KEY`/`ENGINE_BINANCE_API_SECRET`. Рекомендуется тестнет (`ENGINE_BINANCE_USE_TESTNET=true`) до полного прохождения интеграционных тестов.

## Переменные окружения

См. `.env.example` для полного списка. Ключевые параметры:

- `ENGINE_MODE` — `paper` (по умолчанию) или `live`.
- `ENGINE_DATABASE_URL` — строка подключения к БД.
- `ENGINE_BINANCE_API_KEY`/`ENGINE_BINANCE_API_SECRET` — ключи Binance.
- `ENGINE_BINANCE_FUTURES` — переключение между фьючерсами и спотом.
- `ENGINE_POLL_INTERVAL_SECONDS` — период пересчёта стратегий.
- `ENGINE_DEFAULT_LEVERAGE` — плечо по умолчанию для расчёта размера позиции.

## Тестовый прогон

После старта убедитесь, что в таблицах `signals`, `orders`, `positions` появляются новые записи. Для ручной проверки выполните `SELECT * FROM signals ORDER BY created_at DESC LIMIT 5;`.
