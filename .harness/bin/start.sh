#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/runtime.sh"
cd "$HARNESS_ROOT"
exec codex "$@"
