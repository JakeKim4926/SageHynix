#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../bin/runtime.sh"
cd "$HARNESS_ROOT"
"$PY" -m unittest discover -s .harness/tests -v
for script in .harness/bin/*.sh .harness/tests/*.sh; do
  [[ -f "$script" ]] && bash -n "$script"
done
echo 'ALL CHECKS PASSED (unit tests and shell syntax; live Codex not exercised)'
