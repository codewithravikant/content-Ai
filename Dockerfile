# Monorepo image: API + optional Vite SPA (served when frontend/dist exists).
# Build: docker build -t ghostwriter .

FROM node:20-bookworm-slim AS frontend-build
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Pin bookworm: `python:3.11-slim` may track newer Debian (e.g. trixie) where gdk-pixbuf dev package names differ.
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /fe/dist /app/frontend-dist

ENV PYTHONUNBUFFERED=1
ENV GHOSTWRITER_FRONTEND_DIST=/app/frontend-dist

EXPOSE 8000

CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
