#!/usr/bin/env bash
# Backend process entrypoint (also used when Railway "Root Directory" is `backend/`
# — then this file is deployed as /app/railway-entry.sh).
set -euo pipefail
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

if [[ ! -x .venv/bin/python ]]; then
  echo "[FATAL] Missing $BACKEND_DIR/.venv/bin/python — install phase must create backend/.venv" >&2
  ls -la "$BACKEND_DIR" || true
  exit 1
fi

: "${PORT:=8000}"
export PORT
echo "[Content-AI] PORT=$PORT PWD=$BACKEND_DIR — starting uvicorn"

# Railway sits behind a reverse proxy; these help correct client/scheme when needed.
exec .venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips='*'
