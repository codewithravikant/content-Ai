#!/usr/bin/env bash
# Run from service root = backend/ (same layout as local `uvicorn` from backend/).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
