#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/runtime.sh"
exec "$PY" "$HARNESS_ROOT/.codex/hooks/harness_hook.py" "$@"
