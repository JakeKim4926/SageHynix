#!/usr/bin/env bash
# One-shot verification gate. Prints a summary and appends it to .harness/log/verify.log.
# Exit code is non-zero if any executed check failed. Checks that could not run are
# reported as SKIP, never as PASS.
set -uo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$root"
mkdir -p .harness/log
ts="$(date '+%Y-%m-%d %H:%M:%S')"
results=(); status=0

run() {  # run <label> <command...>
  local label="$1"; shift
  local outf; outf="$(mktemp)"
  if "$@" >"$outf" 2>&1; then results+=("PASS  $label")
  else results+=("FAIL  $label"); status=1; echo "----- $label (마지막 30줄)"; tail -n 30 "$outf"; fi
  rm -f "$outf"
}

mapfile -t pyfiles < <(git ls-files '*.py' 2>/dev/null | grep -v '^\.codex/' | grep -v '^\.agents/' || true)
if (( ${#pyfiles[@]} > 0 )); then
  run "python 문법(py_compile)" python3 -m py_compile "${pyfiles[@]}"
  if command -v ruff >/dev/null; then
    run "ruff (오류급 규칙만)" ruff check --select E9,F63,F7,F82 "${pyfiles[@]}"
  else results+=("SKIP  ruff 미설치"); fi
fi
if [[ -d tests ]] && python3 -c 'import pytest' 2>/dev/null; then
  run "pytest" python3 -m pytest -q
elif [[ -d tests ]]; then results+=("SKIP  pytest 미설치 (pip install pytest)")
else results+=("SKIP  tests/ 없음 — 핵심 계산 테스트를 추가할 것"); fi
if [[ -f package.json ]]; then
  run "npm test" npm test --if-present --silent
fi
if [[ -x .harness/verify.local.sh ]]; then
  run "프로젝트 전용 검증(.harness/verify.local.sh)" .harness/verify.local.sh
fi

{
  echo "## verify @ $ts  (HEAD $(git rev-parse --short HEAD 2>/dev/null || echo none))"
  printf '%s\n' "${results[@]}"
} | tee -a .harness/log/verify.log
exit $status
