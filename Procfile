# Procfile for Railway/Heroku (fallback if the platform uses Procfile).
# Use `sh -c` — a bare `cd foo && …` makes the runtime try to exec `cd` (not a real binary).
# Matches repo-root Dockerfile layout: app code in WORKDIR /app (no `cd backend`).
web: sh -c "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"
