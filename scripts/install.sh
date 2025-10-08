#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${1:-https://github.com/example/tranding.git}
INSTALL_DIR=${2:-/opt/tranding}
BRANCH=${3:-main}
PYTHON_BIN=${PYTHON_BIN:-python3}

if [[ $EUID -ne 0 ]]; then
  echo "Запустите скрипт от root (sudo)." >&2
  exit 1
fi

echo "[+] Установка системных зависимостей"
apt-get update -y
apt-get install -y git $PYTHON_BIN $PYTHON_BIN-venv $PYTHON_BIN-dev build-essential redis-server postgresql-client

if [[ ! -d "$INSTALL_DIR" ]]; then
  echo "[+] Клонирую репозиторий $REPO_URL в $INSTALL_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
else
  echo "[+] Репозиторий уже существует, обновляю"
  git -C "$INSTALL_DIR" fetch
  git -C "$INSTALL_DIR" checkout "$BRANCH"
  git -C "$INSTALL_DIR" pull --ff-only
fi

cd "$INSTALL_DIR"

if [[ ! -d .venv ]]; then
  echo "[+] Создаю виртуальное окружение"
  $PYTHON_BIN -m venv .venv
fi

source .venv/bin/activate
pip install -U pip

echo "[+] Устанавливаю зависимости шлюза"
pip install -e services/gateway

echo "[+] Устанавливаю зависимости торгового движка"
pip install -e services/trading_engine

if [[ ! -f services/gateway/.env ]]; then
  cp services/gateway/.env.example services/gateway/.env
  echo "Создан services/gateway/.env — заполните значения перед запуском"
fi

if [[ ! -f services/trading_engine/.env ]]; then
  cp services/trading_engine/.env.example services/trading_engine/.env
  echo "Создан services/trading_engine/.env — задайте ключи Binance и настройки режима"
fi

echo "[+] Генерирую unit-файлы systemd"
cat >/etc/systemd/system/trading-gateway.service <<SERVICE
[Unit]
Description=Trading Gateway API
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR/services/gateway
ExecStart=$INSTALL_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Environment=PYTHONPATH=$INSTALL_DIR/services/gateway
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

cat >/etc/systemd/system/trading-engine.service <<SERVICE
[Unit]
Description=Trading Engine
After=network.target trading-gateway.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR/services/trading_engine
ExecStart=$INSTALL_DIR/.venv/bin/trading-engine
Environment=PYTHONPATH=$INSTALL_DIR
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable trading-gateway.service trading-engine.service

echo "[+] Установка завершена"
echo "Заполните .env файлы и запустите сервисы командой: systemctl start trading-gateway trading-engine"
