#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
alembic upgrade head
python -m backend.app.db.bootstrap
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --env-file .env
