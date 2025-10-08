# Tranding Platform Blueprint

Этот репозиторий содержит спецификацию, FastAPI-шлюз и асинхронный торговый движок для работы с Binance.

- [System Specification](docs/system_spec.md)
- [Gateway Service](services/gateway/README.md)
- [Trading Engine](services/trading_engine/README.md)

## Запуск шлюза

Краткое руководство по установке зависимостей и запуску FastAPI-шлюза находится в разделе ["Быстрый старт"](services/gateway/README.md#быстрый-старт).
Следуйте шагам из README сервиса: клонирование, настройка виртуального окружения, копирование `.env.example` и старт `uvicorn`.

## Запуск торгового движка

Подробный гайд находится в [`services/trading_engine/README.md`](services/trading_engine/README.md).
Движок устанавливается в то же виртуальное окружение, что и шлюз, и стартует командой `trading-engine`.

## Автоматическая установка на Ubuntu

Для развёртывания полного стека на чистой Ubuntu выполните:

```bash
curl -fsSL https://raw.githubusercontent.com/example/tranding/main/scripts/install.sh | sudo bash -s -- https://github.com/example/tranding.git /opt/tranding main
```

Скрипт установит системные зависимости, создаст виртуальное окружение, установит пакеты шлюза и движка, а также подготовит unit-файлы `systemd`. После заполнения `.env` файлов запустите сервисы командами `systemctl start trading-gateway trading-engine`.
