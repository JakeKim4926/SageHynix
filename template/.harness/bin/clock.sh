#!/usr/bin/env bash
# Exam timer shared by every terminal, worktree and the Codex hooks.
#   clock.sh start [-f] [minutes]   start the timer (default 180)
#   clock.sh status                 elapsed / remaining / phase
set -euo pipefail
STATE="${HYNIX_HARNESS_HOME:-$HOME/.hynix-harness}"
CLOCK="$STATE/clock.json"
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/.codex/hooks/harness_hook.py"
mkdir -p "$STATE"

case "${1:-status}" in
  start)
    shift
    force=0
    if [[ "${1:-}" == "-f" ]]; then force=1; shift; fi
    minutes="${1:-180}"
    if [[ -f "$CLOCK" && $force -eq 0 ]]; then
      echo "이미 시작됨: $(cat "$CLOCK")  (재설정은 -f)"; exit 1
    fi
    printf '{"start": %s, "minutes": %s}\n' "$(date +%s)" "$minutes" > "$CLOCK"
    echo "타이머 시작: ${minutes}분 ($(date '+%H:%M:%S'))"
    ;;
  status)
    if [[ ! -f "$CLOCK" ]]; then echo "타이머 미시작 (clock.sh start)"; exit 0; fi
    echo '{"hook_event_name":"UserPromptSubmit","model":"","prompt":""}' \
      | HYNIX_HARNESS_HOME="$STATE" HYNIX_HARNESS_NOLOG=1 python3 "$HOOK" prompt \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])'
    ;;
  *) echo "usage: clock.sh start [-f] [minutes] | status"; exit 2 ;;
esac
