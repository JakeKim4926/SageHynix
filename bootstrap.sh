#!/usr/bin/env bash
# Apply the root harness to an existing task workspace; preserve its files.
set -euo pipefail
source "$(dirname "$0")/.harness/bin/runtime.sh"
if (( $# == 0 )); then
  echo 'usage: bash bootstrap.sh /path/to/task-workspace [--no-commit]' >&2
  exit 2
fi
exec "$PY" "$HARNESS_ROOT/.harness/bin/install_workspace.py" "$@"
