SHELL := /bin/bash
.DEFAULT_GOAL := help

REPO_ROOT := $(CURDIR)
BACKEND_DIR := $(REPO_ROOT)/backend
FRONTEND_DIR := $(REPO_ROOT)/frontend

BACKEND_VENV := $(BACKEND_DIR)/venv
BACKEND_PORT := 8000
FRONTEND_PORT := 3000
MAILPIT_IMAGE := axllent/mailpit

# Helpful when you want verbose output:
#   make DEV_VERBOSE=1 dev
DEV_VERBOSE ?= 0
ifeq ($(DEV_VERBOSE),1)
VERBOSE_FLAG :=
else
VERBOSE_FLAG := @
endif

.PHONY: help
help:
	@echo "Ghostwriter — Makefile"
	@echo ""
	@echo "Setup & run"
	@echo "  make configure       Interactive: set OPENROUTER_* in backend/.env"
	@echo "  make configure-root  Same + update repo root .env (OpenRouter vars only)"
	@echo "  make init-env        Alias for configure"
	@echo "  make setup           Install backend + frontend dependencies (idempotent)"
	@echo "  make dev             Start backend + frontend (Ctrl+C stops both)"
	@echo "  make health          Check backend http://localhost:$(BACKEND_PORT)/health"
	@echo "  make test            Backend pytest + frontend lint"
	@echo "  make sanity          health + tests + lint"
	@echo "  make security        pip-audit (backend) + npm audit (frontend)"
	@echo "  make encrypt-env     Encrypt local .env → .env.enc (needs ENV_PASSPHRASE)"
	@echo "  make decrypt-env     Decrypt .env.enc → .env"
	@echo "  make clean           Remove venv + node_modules"
	@echo ""
	@echo "Email verification (login with GHOSTWRITER_REQUIRE_EMAIL_LOGIN=true)"
	@echo "  make email-help      How to run Mailpit or Resend (read this first)"
	@echo "  make mailpit         Start Mailpit: SMTP :1025, web UI :8025 (needs Docker)"
	@echo ""
	@echo "Notes"
	@echo "  - Backend loads backend/.env; frontend loads frontend/.env (Vite)."
	@echo "  - First run: make configure, or cp backend/.env.example backend/.env"

.PHONY: configure
configure: check-tools
	@"$(REPO_ROOT)/scripts/configure-env.sh"

.PHONY: init-env
init-env: configure

.PHONY: configure-root
configure-root: check-tools
	@"$(REPO_ROOT)/scripts/configure-env.sh" --root

.PHONY: check-tools
check-tools:
	$(VERBOSE_FLAG) command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }
	$(VERBOSE_FLAG) command -v node >/dev/null 2>&1 || { echo "node not found"; exit 1; }
	$(VERBOSE_FLAG) command -v npm >/dev/null 2>&1 || { echo "npm not found"; exit 1; }
	$(VERBOSE_FLAG) command -v curl >/dev/null 2>&1 || { echo "curl not found"; exit 1; }

.PHONY: check-python
check-python:
	$(VERBOSE_FLAG) python3 -c 'import sys; v=sys.version_info; assert v >= (3,11), f"Python 3.11+ required; found {sys.version}"'

.PHONY: check-node
check-node:
	$(VERBOSE_FLAG) node -e "const [major]=process.versions.node.split('.'); if (+major < 18) { throw new Error('Node 18+ required'); }"

.PHONY: setup-backend
setup-backend: check-tools check-python
	$(VERBOSE_FLAG) if [[ ! -d "$(BACKEND_VENV)" ]]; then \
		echo "Creating backend venv at $(BACKEND_VENV)"; \
		python3 -m venv "$(BACKEND_VENV)"; \
	fi
	$(VERBOSE_FLAG) source "$(BACKEND_VENV)/bin/activate" && \
		python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
	$(VERBOSE_FLAG) source "$(BACKEND_VENV)/bin/activate" && \
		pip install -r "$(BACKEND_DIR)/requirements.txt"

.PHONY: setup-frontend
setup-frontend: check-tools check-node
	$(VERBOSE_FLAG) if [[ ! -d "$(FRONTEND_DIR)/node_modules" ]]; then \
		echo "Installing frontend dependencies"; \
		cd "$(FRONTEND_DIR)" && npm ci; \
	fi

.PHONY: setup
setup: setup-backend setup-frontend
	@echo "Setup complete."

.PHONY: dev-backend
dev-backend:
	@set -euo pipefail; \
	if [[ ! -f "$(BACKEND_DIR)/.env" ]]; then \
		echo "Missing $(BACKEND_DIR)/.env"; \
		echo "Run: make configure   (interactive prompt for OpenRouter key and model)"; \
		echo "Or:  cp backend/.env.example backend/.env  and edit OPENROUTER_* manually."; \
		exit 1; \
	fi; \
	echo "Starting backend on http://localhost:$(BACKEND_PORT)"; \
	cd "$(BACKEND_DIR)" && \
	source "$(BACKEND_VENV)/bin/activate" && \
	set -a && source .env && set +a && \
	uvicorn app.main:app --reload --host 0.0.0.0 --port "$(BACKEND_PORT)"

.PHONY: dev-frontend
dev-frontend:
	@echo "Starting frontend on http://localhost:$(FRONTEND_PORT)"; \
	cd "$(FRONTEND_DIR)" && npm run dev -- --host 0.0.0.0 --port "$(FRONTEND_PORT)"

.PHONY: dev
dev: setup
	@set -euo pipefail; \
		echo "Launching backend + frontend (Ctrl+C to stop)"; \
		( $(MAKE) dev-backend ) & pid1=$$!; \
		( $(MAKE) dev-frontend ) & pid2=$$!; \
		trap 'echo "Stopping..."; kill $$pid1 $$pid2 2>/dev/null || true' INT TERM; \
		wait $$pid1 $$pid2

.PHONY: health
health:
	@echo "Checking backend health at http://localhost:$(BACKEND_PORT)/health"; \
	code=0; \
	for i in {1..30}; do \
		resp="$$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$(BACKEND_PORT)/health" || true)"; \
		if [[ "$$resp" == "200" ]]; then code=0; break; fi; \
		code=1; \
		echo "Waiting... ($$i/30)"; \
		sleep 1; \
	done; \
	if [[ "$$code" != "0" ]]; then \
		echo "Health check failed. Try make dev first."; \
		exit 1; \
	fi; \
	echo "Backend is healthy."

.PHONY: test
test: setup
	@echo "Running backend tests"; \
	source "$(BACKEND_VENV)/bin/activate"; \
	cd "$(BACKEND_DIR)" && pytest -q; \
	echo "Running frontend lint"; \
	cd "$(FRONTEND_DIR)" && npm run lint

.PHONY: sanity
sanity: health test
	@echo "Sanity check passed."

.PHONY: security
security: setup
	@echo "--- Backend security audit (pip-audit) ---"; \
	source "$(BACKEND_VENV)/bin/activate" && \
		pip install -q pip-audit && \
		pip-audit -r "$(BACKEND_DIR)/requirements.txt" --format=columns; \
	echo ""; \
	echo "--- Frontend security audit (npm audit) ---"; \
	cd "$(FRONTEND_DIR)" && npm audit --audit-level=high || true

.PHONY: encrypt-env
encrypt-env: check-tools
	@set -euo pipefail; \
	command -v openssl >/dev/null 2>&1 || { echo "openssl not found"; exit 1; }; \
	if [[ -z "$${ENV_PASSPHRASE:-}" ]]; then \
		echo "ENV_PASSPHRASE is required."; \
		echo "Example: ENV_PASSPHRASE='your-strong-passphrase' make encrypt-env"; \
		exit 1; \
	fi; \
	if [[ -f "$(BACKEND_DIR)/.env" ]]; then \
		openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
			-in "$(BACKEND_DIR)/.env" \
			-out "$(BACKEND_DIR)/.env.enc" \
			-pass env:ENV_PASSPHRASE; \
		chmod 600 "$(BACKEND_DIR)/.env.enc"; \
		echo "Encrypted: $(BACKEND_DIR)/.env -> .env.enc"; \
	else \
		echo "Skipped: $(BACKEND_DIR)/.env not found"; \
	fi; \
	if [[ -f "$(FRONTEND_DIR)/.env" ]]; then \
		openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
			-in "$(FRONTEND_DIR)/.env" \
			-out "$(FRONTEND_DIR)/.env.enc" \
			-pass env:ENV_PASSPHRASE; \
		chmod 600 "$(FRONTEND_DIR)/.env.enc"; \
		echo "Encrypted: $(FRONTEND_DIR)/.env -> .env.enc"; \
	else \
		echo "Skipped: $(FRONTEND_DIR)/.env not found"; \
	fi; \
	echo "Local encryption complete. Plain .env files are still present."

.PHONY: decrypt-env
decrypt-env: check-tools
	@set -euo pipefail; \
	command -v openssl >/dev/null 2>&1 || { echo "openssl not found"; exit 1; }; \
	if [[ -z "$${ENV_PASSPHRASE:-}" ]]; then \
		echo "ENV_PASSPHRASE is required."; \
		echo "Example: ENV_PASSPHRASE='your-strong-passphrase' make decrypt-env"; \
		exit 1; \
	fi; \
	if [[ -f "$(BACKEND_DIR)/.env.enc" ]]; then \
		openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
			-in "$(BACKEND_DIR)/.env.enc" \
			-out "$(BACKEND_DIR)/.env" \
			-pass env:ENV_PASSPHRASE; \
		chmod 600 "$(BACKEND_DIR)/.env"; \
		echo "Decrypted: $(BACKEND_DIR)/.env.enc -> .env"; \
	else \
		echo "Skipped: $(BACKEND_DIR)/.env.enc not found"; \
	fi; \
	if [[ -f "$(FRONTEND_DIR)/.env.enc" ]]; then \
		openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
			-in "$(FRONTEND_DIR)/.env.enc" \
			-out "$(FRONTEND_DIR)/.env" \
			-pass env:ENV_PASSPHRASE; \
		chmod 600 "$(FRONTEND_DIR)/.env"; \
		echo "Decrypted: $(FRONTEND_DIR)/.env.enc -> .env"; \
	else \
		echo "Skipped: $(FRONTEND_DIR)/.env.enc not found"; \
	fi; \
	echo "Local decryption complete."

.PHONY: clean
clean:
	@echo "Cleaning local install artifacts (venv + node_modules)"; \
	rm -rf "$(BACKEND_VENV)" "$(FRONTEND_DIR)/node_modules"

.PHONY: email-help
email-help:
	@echo "Ghostwriter — email verification for local login"
	@echo ""
	@echo "1) Enable login in backend/.env:"
	@echo "     GHOSTWRITER_REQUIRE_EMAIL_LOGIN=true"
	@echo ""
	@echo "2) Pick how mail is sent (choose one):"
	@echo ""
	@echo "   A) Local Mailpit (default SMTP, good for dev)"
	@echo "      - In another terminal:  make mailpit"
	@echo "      - Keeps defaults: SMTP_HOST=localhost SMTP_PORT=1025"
	@echo "      - Open the inbox:     http://localhost:8025"
	@echo "      - Restart the API after changing backend/.env"
	@echo ""
	@echo "   B) Resend (real inbox, HTTP API)"
	@echo "      - In backend/.env set:"
	@echo "          EMAIL_BACKEND=resend"
	@echo "          RESEND_API_KEY=re_xxxxxxxx"
	@echo "          RESEND_FROM=onboarding@resend.dev   # or your verified domain"
	@echo "      - Create a key at https://resend.com/api-keys"
	@echo "      - Restart the API"
	@echo ""
	@echo "3) Run the app:  make dev"
	@echo "   The sign-in dialog explains Mailpit vs Resend based on your config."
	@echo ""

.PHONY: mailpit
mailpit: check-tools
	@command -v docker >/dev/null 2>&1 || { \
		echo "Docker is required for this shortcut."; \
		echo "Install Docker Desktop, or run Mailpit manually — see: make email-help"; \
		exit 1; \
	}
	@echo "Starting Mailpit — SMTP localhost:1025  |  Web UI http://localhost:8025"
	@echo "Press Ctrl+C to stop."
	@echo ""
	docker run --rm -p 1025:1025 -p 8025:8025 $(MAILPIT_IMAGE)

