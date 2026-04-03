#!/usr/bin/env bash
# Backwards-compatible alias for local docs / scripts.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/railway-entry.sh"
