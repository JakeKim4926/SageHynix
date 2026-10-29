#!/usr/bin/env bash
# Parallel research with independent `codex exec` processes (fallback when in-session
# subagents are unavailable, or when you want each lane as its own visible CLI session).
#
#   fanout.sh <lanes-file> [max-parallel=3]
#
# lanes-file: one lane per line, "name|question". Lines starting with # are ignored.
# Each lane runs read-only and writes its final answer to docs/research/<name>.md.
# Env: CODEX_BIN (default: codex), FANOUT_ARGS (extra exec args, e.g. "-m gpt-6.1-sol").
set -uo pipefail
CODEX_BIN="${CODEX_BIN:-codex}"
read -r -a extra <<< "${FANOUT_ARGS:-}"
lanes="${1:?lanes-file 필요 (name|question 형식)}"
max="${2:-3}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
out="$root/docs/research"; logs="$root/.harness/log"
mkdir -p "$out" "$logs"

rules='규칙: 너는 독립 조사 레인이다. 파일을 수정하지 말고 조사·실행·정리만 한다. 실행해서 확인한 사실과 추정을 구분해 표시하고, 확인 못 한 것은 "미확인"으로 적는다. 마지막 답변은 Markdown 보고서 하나로: ## 결론(3줄) / ## 근거(명령·파일:줄·URL) / ## 불확실성 / ## 업무 담당자에게 물을 질문.'

pids=(); names=()
while IFS='|' read -r name question; do
  [[ -z "${name// }" || "$name" =~ ^# ]] && continue
  while (( $(jobs -rp | wc -l) >= max )); do sleep 2; done
  echo "▶ lane '$name' 시작"
  "$CODEX_BIN" exec --sandbox read-only -C "$root" \
    -c 'model_reasoning_effort="medium"' ${extra[@]+"${extra[@]}"} \
    -o "$out/$name.md" \
    "$question

$rules" > "$logs/fanout-$name.log" 2>&1 < /dev/null &
  pids+=($!); names+=("$name")
done < "$lanes"

fail=0
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then echo "✔ ${names[$i]} → docs/research/${names[$i]}.md"
  else echo "✘ ${names[$i]} 실패 (로그: .harness/log/fanout-${names[$i]}.log)"; fail=1; fi
done
echo 'Next: ask Codex "$parallel-research 결과 종합" -> docs/research/SYNTHESIS.md'
exit $fail
