#!/usr/bin/env bash
# Monorepo: run API from repo root (same as `cd backend && uvicorn ...`).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
