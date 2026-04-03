#!/usr/bin/env bash
# Monorepo only: delegates to backend/railway-entry.sh.
# Not present when Railway deploys with "Root Directory" = backend (use bash railway-entry.sh there too).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/backend/railway-entry.sh"
