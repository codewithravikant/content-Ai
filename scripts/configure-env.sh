#!/usr/bin/env bash
# Interactive bootstrap: writes OPENROUTER_API_KEY and OPENROUTER_MODEL to backend/.env
# (and optionally root .env). Safe for special characters in values (uses Python upsert).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_ENV="${REPO_ROOT}/backend/.env"
BACKEND_EXAMPLE="${REPO_ROOT}/backend/.env.example"
ROOT_ENV="${REPO_ROOT}/.env"
ROOT_EXAMPLE="${REPO_ROOT}/.env.example"

INCLUDE_ROOT=0
for arg in "$@"; do
  case "$arg" in
    --root) INCLUDE_ROOT=1 ;;
    -h|--help)
      echo "Usage: $0 [--root]"
      echo "  Prompts for OpenRouter API key (hidden) and optional model."
      echo "  Creates backend/.env from backend/.env.example if needed."
      echo "  --root  Also create/update repo root .env with the same OpenRouter vars."
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$BACKEND_EXAMPLE" ]]; then
  echo "Missing $BACKEND_EXAMPLE" >&2
  exit 1
fi

if [[ ! -f "$BACKEND_ENV" ]]; then
  cp "$BACKEND_EXAMPLE" "$BACKEND_ENV"
  chmod 600 "$BACKEND_ENV"
  echo "Created $BACKEND_ENV from example."
fi

if [[ ! -r /dev/tty ]]; then
  echo "No TTY (e.g. CI or piped stdin). Run this script in an interactive terminal." >&2
  echo "Non-interactive: copy backend/.env.example to backend/.env and set OPENROUTER_* manually." >&2
  exit 1
fi

echo -n "OpenRouter API key (input hidden): " >&2
read -r -s API_KEY </dev/tty
echo "" >&2

if [[ -z "${API_KEY// }" ]]; then
  echo "Error: API key cannot be empty." >&2
  exit 1
fi

DEFAULT_MODEL=""
if grep -qE '^OPENROUTER_MODEL=' "$BACKEND_ENV" 2>/dev/null; then
  DEFAULT_MODEL="$(grep -E '^OPENROUTER_MODEL=' "$BACKEND_ENV" | head -1 | cut -d= -f2-)"
fi
if [[ -z "$DEFAULT_MODEL" ]] && grep -qE '^OPENROUTER_MODEL=' "$BACKEND_EXAMPLE" 2>/dev/null; then
  DEFAULT_MODEL="$(grep -E '^OPENROUTER_MODEL=' "$BACKEND_EXAMPLE" | head -1 | cut -d= -f2-)"
fi
[[ -z "$DEFAULT_MODEL" ]] && DEFAULT_MODEL="openai/gpt-3.5-turbo"

echo -n "OpenRouter model [${DEFAULT_MODEL}]: " >&2
read -r MODEL_INPUT </dev/tty
MODEL="${MODEL_INPUT:-$DEFAULT_MODEL}"
if [[ -z "${MODEL// }" ]]; then
  echo "Error: model cannot be empty." >&2
  exit 1
fi

if [[ "$INCLUDE_ROOT" -eq 1 ]]; then
  if [[ ! -f "$ROOT_EXAMPLE" ]]; then
    echo "Skipping root .env: $ROOT_EXAMPLE not found." >&2
    INCLUDE_ROOT=0
  elif [[ ! -f "$ROOT_ENV" ]]; then
    cp "$ROOT_EXAMPLE" "$ROOT_ENV"
    chmod 600 "$ROOT_ENV"
    echo "Created $ROOT_ENV from example."
  fi
fi

export BACKEND_ENV ROOT_ENV API_KEY MODEL INCLUDE_ROOT
python3 <<'PY'
import os
import re

key = os.environ["API_KEY"]
model = os.environ["MODEL"]
include_root = os.environ.get("INCLUDE_ROOT", "0") == "1"


def upsert(lines: list[str], name: str, value: str) -> list[str]:
    out: list[str] = []
    found = False
    prefix = name + "="
    pat = re.compile(rf"^{re.escape(name)}\s*=")
    for line in lines:
        if line.lstrip().startswith("#"):
            out.append(line)
            continue
        if line.startswith(prefix) or pat.match(line):
            out.append(f"{name}={value}\n")
            found = True
        else:
            out.append(line)
    if not found:
        if out and not out[-1].endswith("\n"):
            out[-1] = out[-1] + "\n"
        out.append(f"{name}={value}\n")
    return out


def patch(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = upsert(lines, "OPENROUTER_API_KEY", key)
    lines = upsert(lines, "OPENROUTER_MODEL", model)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)


patch(os.environ["BACKEND_ENV"])
if include_root and os.path.isfile(os.environ["ROOT_ENV"]):
    patch(os.environ["ROOT_ENV"])
PY

chmod 600 "$BACKEND_ENV"
echo "Updated $BACKEND_ENV (OPENROUTER_API_KEY, OPENROUTER_MODEL)."
if [[ "$INCLUDE_ROOT" -eq 1 ]] && [[ -f "$ROOT_ENV" ]]; then
  chmod 600 "$ROOT_ENV"
  echo "Updated $ROOT_ENV (OPENROUTER_API_KEY, OPENROUTER_MODEL)."
fi

echo "" >&2
echo "Tip: shell history may record commands; this script does not echo your key." >&2
echo "Next: make setup && make dev" >&2
