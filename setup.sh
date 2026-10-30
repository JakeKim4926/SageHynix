#!/usr/bin/env bash
# Initialize this checkout; install only explicitly selected optional profiles.
set -euo pipefail
source "$(dirname "$0")/.harness/bin/runtime.sh"
exec "$PY" "$HARNESS_ROOT/.harness/bin/environment.py" setup "$@"
