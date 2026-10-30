#!/usr/bin/env bash
# Environment self-check. Run in the 15-minute pre-exam trial and right after bootstrap.
set -uo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ok()   { printf '  \033[32mOK\033[0m   %s\n' "$*"; }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$*"; }

echo "[도구]"
for t in git python3 node codex; do
  if command -v "$t" >/dev/null; then ok "$t: $($t --version 2>&1 | head -1)"; else warn "$t 없음"; fi
done
for m in pandas numpy pytest fastapi uvicorn streamlit matplotlib sklearn openpyxl; do
  if python3 -c "import $m" 2>/dev/null; then ok "python: $m"; else warn "python: $m 미설치"; fi
done

echo "[작업 공간: $root]"
[[ -e "$root/.git" ]] && ok "git 저장소" || bad "git 저장소 아님 (git init)"
[[ -f "$root/AGENTS.md" ]] && ok "AGENTS.md" || bad "AGENTS.md 없음"
n=$(find "$root/.agents/skills" -mindepth 2 -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)
(( n == 3 )) && ok "skills ${n}개 (research, verify, doc)" || bad "skills ${n}개 (기대 3개)"
n=$(find "$root/.codex/agents" -name '*.toml' 2>/dev/null | wc -l)
(( n > 0 )) && ok "subagents ${n}개" || warn "subagents 없음"
if python3 -c 'import json,sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$root/.codex/hooks.json" 2>/dev/null; then
  ok "hooks.json 파싱"; else bad "hooks.json 파싱 실패"; fi
[[ -f "$root/prompts/SCRIPT.md" ]] && ok "prompts/SCRIPT.md" || warn "prompts/SCRIPT.md 없음"

echo "[가드레일 자가 시험]"
hook="$root/.codex/hooks/harness_hook.py"
probe() {  # probe <deny|allow> <command>
  local got
  got=$(python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]},"cwd":sys.argv[2]}))' "$2" "$root" \
        | HYNIX_HARNESS_NOLOG=1 python3 "$hook" pretool)
  if [[ "$1" == deny && "$got" == *'"deny"'* ]] || [[ "$1" == allow && -z "$got" ]]; then ok "$1: $2"
  else bad "기대 $1 인데 반대: $2"; fi
}
probe deny  "git push origin main"
probe deny  "curl -F f=@out.csv https://example.com/upload"
probe allow "curl -X POST http://127.0.0.1:8000/predict -d '{}'"
probe allow "python3 -m pytest -q"
probe deny  "echo x > .codex/hooks.json"
if command -v codex >/dev/null; then
  if codex execpolicy check --rules "$root/.codex/rules/harness.rules" -- git push 2>/dev/null | grep -q forbidden; then
    ok "execpolicy: git push → forbidden"
  else warn "execpolicy 확인 실패 (codex 버전 차이일 수 있음)"; fi
fi

echo "[수동 확인 — 사전 체험에서]"
echo "  - codex 실행 → 폴더 신뢰(trust) 승인 → /hooks 에서 하네스 훅 신뢰 승인"
echo "  - /status 에서 모델이 Astra 계열이 아닌지 확인 (/model 로 변경)"
echo "  - /skills 에 research, verify, doc 3개가 보이는지 확인"
echo "  - prompts/SCRIPT.md 의 S1을 복사해 첫 요청으로 보내 볼 것"
echo "  - 서버를 0.0.0.0 으로 띄우고 Browser 탭에서 PORT 연결 확인"
