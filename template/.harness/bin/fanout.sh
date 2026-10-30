#!/usr/bin/env bash
# Parallel research with independent `codex exec` processes (fallback when in-session
# subagents are unavailable, or when you want each lane as its own visible CLI session).
#
#   fanout.sh <lanes-file> [max-parallel=3]
#
# lanes-file: one lane per line, "name|question". Lines starting with # are ignored.
# Each lane is a ctx entry research/<name>: lanes that are already valid are skipped (reuse),
# the rest run read-only and write ctx/research/<name>/report.md, then `ctx.py done` checks them.
# Env: CODEX_BIN (default: codex), FANOUT_ARGS (extra exec args, e.g. "-m gpt-6.1-sol"),
#      FANOUT_FORCE=1 (re-run valid lanes too).
set -uo pipefail
CODEX_BIN="${CODEX_BIN:-codex}"
read -r -a extra <<< "${FANOUT_ARGS:-}"
lanes="${1:?lanes-file 필요 (name|question 형식)}"
max="${2:-3}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PY="$(command -v python3 || command -v python)"
ctx() { "$PY" "$root/.harness/bin/ctx.py" "$@"; }
out="$root/ctx/research"; logs="$root/.harness/log"
mkdir -p "$out" "$logs"

rules='규칙: 너는 독립 조사 레인이다. 파일을 수정하지 말고 조사·실행·정리만 한다. 실행해서 확인한 사실과 추정을 구분해 [사실]/[추론]으로 표시하고, 확인 못 한 것은 "미확인"으로 적는다. 마지막 답변은 Markdown 보고서 하나로, 다음 섹션을 모두 채운다: ## 결론(3줄 이내, 첫 줄이 한 줄 요약) / ## 선택지(이름 | 충족 요구사항 | 비용 | 위험, 없으면 "없음") / ## 근거(명령·파일:줄·URL) / ## 미확인(없으면 "없음") / ## 담당자 질문.'

pids=(); names=(); fail=0
while IFS='|' read -r name question; do
  [[ -z "${name// }" || "$name" =~ ^# ]] && continue
  if [[ -z "${FANOUT_FORCE:-}" && "$(ctx state "research/$name")" == valid ]]; then
    echo "♻ lane '$name' valid 기록 재사용 (ctx.py get research/$name)"; continue
  fi
  if ! ctx new research "$name" --q "$question" --redo >/dev/null; then
    echo "✘ lane '$name' 등록 실패 (이름은 영문 소문자·숫자·-)"; fail=1; continue
  fi
  while (( $(jobs -rp | wc -l) >= max )); do sleep 2; done
  echo "▶ lane '$name' 시작"
  "$CODEX_BIN" exec --sandbox read-only -C "$root" \
    -c 'model_reasoning_effort="medium"' ${extra[@]+"${extra[@]}"} \
    -o "$out/$name/report.md" \
    "$question

$rules" > "$logs/fanout-$name.log" 2>&1 < /dev/null &
  pids+=($!); names+=("$name")
done < "$lanes"

for i in "${!pids[@]}"; do
  n="${names[$i]}"
  if ! wait "${pids[$i]}"; then echo "✘ $n 실패 (로그: .harness/log/fanout-$n.log), draft로 남음"; fail=1
  elif ctx done "research/$n" >/dev/null; then echo "✔ $n → ctx/research/$n/report.md (valid)"
  else echo "✘ $n 형식 미달 — \`ctx.py done research/$n\` 로 이유 확인 후 보완"; fail=1; fi
done
echo 'Next: ask Codex "$research-in-parallel 결과 종합" -> ctx/research/synthesis'
exit $fail
