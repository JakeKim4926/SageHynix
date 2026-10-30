#!/usr/bin/env bash
# Source from harness scripts; resolve a working interpreter, not a PATH alias.
HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HARNESS_MAIN_ROOT="$HARNESS_ROOT"
common=$(git -C "$HARNESS_ROOT" rev-parse --git-common-dir 2>/dev/null || true)
if [[ -n "$common" ]]; then
  HARNESS_MAIN_ROOT=$(cd "$HARNESS_ROOT" && cd "$common" && cd .. && pwd) || return 1
fi
export HYNIX_HARNESS_HOME="${HYNIX_HARNESS_HOME:-$HARNESS_MAIN_ROOT/.harness/state}"
harness_python() {
  local candidate
  for candidate in "$HARNESS_ROOT/.venv/bin/python3" "$HARNESS_ROOT/.venv/Scripts/python.exe" "$HARNESS_MAIN_ROOT/.venv/bin/python3" "$HARNESS_MAIN_ROOT/.venv/Scripts/python.exe" python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
      PY="$candidate"; export PY; return 0
    fi
  done
  echo 'FAIL: 실행 가능한 Python 3.9+가 없습니다. docs/SETUP.md의 복구 안내를 확인하세요.' >&2
  return 1
}
harness_python || return 1
if [[ "$PY" == */.venv/* ]]; then export PATH="$(dirname "$PY"):$PATH"; fi
