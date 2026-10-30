#!/usr/bin/env bash
# Install the harness into an exam workspace. Non-destructive: never overwrites
# existing files and never touches ~/.codex/config.toml (platform-managed).
#
#   bash bootstrap.sh [WORKSPACE=$PWD] [--no-commit]
#
# Typical exam use:
#   git clone https://github.com/JakeKim4926/SageHynix ~/harness
#   bash ~/harness/bootstrap.sh ~/workspace
set -euo pipefail

HARNESS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${1:-$PWD}"; [[ "$WS" == --* ]] && WS="$PWD"
COMMIT=1; for a in "$@"; do [[ "$a" == "--no-commit" ]] && COMMIT=0; done
WS="$(cd "$WS" && pwd)"
STATE="${HYNIX_HARNESS_HOME:-$HOME/.hynix-harness}"

say() { printf '\033[36m[harness]\033[0m %s\n' "$*"; }
copied=(); skipped=()

copy_tree() {  # copy_tree <src-dir> <dst-dir> : copy files that do not exist yet
  local src="$1" dst="$2" rel
  while IFS= read -r -d '' f; do
    rel="${f#"$src"/}"
    if [[ -e "$dst/$rel" ]]; then skipped+=("$rel")
    else mkdir -p "$(dirname "$dst/$rel")"; cp "$f" "$dst/$rel"; copied+=("$rel"); fi
  done < <(find "$src" -type f -print0)
}

say "workspace: $WS"
[[ "$WS" == "$HARNESS" ]] && { echo "하네스 저장소 자체에는 설치하지 않습니다. 작업 공간 경로를 주세요."; exit 2; }

# 1) AGENTS.md: never overwrite an organizer-provided one.
if cmp -s "$HARNESS/template/AGENTS.md" "$WS/AGENTS.md"; then
  skipped+=("AGENTS.md")
elif [[ -e "$WS/AGENTS.md" ]]; then
  cp "$HARNESS/template/AGENTS.md" "$WS/AGENTS.harness.md"
  say "⚠ 기존 AGENTS.md가 있어 건드리지 않았습니다. 하네스 규칙은 AGENTS.harness.md 로 저장."
  say "   내용 확인 후 직접 합치려면:  cat AGENTS.harness.md >> AGENTS.md"
else
  cp "$HARNESS/template/AGENTS.md" "$WS/AGENTS.md"; copied+=("AGENTS.md")
fi

# 2) Codex project layer, harness scripts, doc skeleton.
for d in .codex .harness docs ctx; do copy_tree "$HARNESS/template/$d" "$WS/$d"; done

# 3) Skills (single source: plugins/hynix-harness/skills) -> repo-scoped skills.
copy_tree "$HARNESS/plugins/hynix-harness/skills" "$WS/.agents/skills"

chmod +x "$WS"/.harness/bin/*.sh "$WS"/.harness/bin/*.py "$WS"/.codex/hooks/*.py "$WS"/.agents/skills/*/scripts/*.py 2>/dev/null || true

# 4) Keep logs out of git (they are still files in the workspace).
touch "$WS/.gitignore"
grep -qxF '.harness/log/' "$WS/.gitignore" || printf '\n# harness runtime logs\n.harness/log/\n__pycache__/\n' >> "$WS/.gitignore"

# 4b) ctx/ work memory: INDEX.md is regenerated from index.jsonl, and the append-only
#     event log merges as a union so worktree lanes never conflict on it.
grep -qxF 'ctx/INDEX.md' "$WS/.gitignore" || printf 'ctx/INDEX.md\nctx/.INDEX.*.tmp\n' >> "$WS/.gitignore"
touch "$WS/.gitattributes"
grep -qxF 'ctx/index.jsonl merge=union' "$WS/.gitattributes" || printf 'ctx/index.jsonl merge=union\n' >> "$WS/.gitattributes"
PY="$(command -v python3 || command -v python)"
CTX_ROOT="$WS" "$PY" "$WS/.harness/bin/ctx.py" init >/dev/null

# 5) Shared state for hooks/clock across terminals and worktrees.
mkdir -p "$STATE"; printf '%s\n' "$WS" > "$STATE/workspace"

# 6) Git: worktree lanes need the harness committed.
cd "$WS"
if [[ ! -e .git ]]; then git init -q; say "git init (작업 공간이 저장소가 아니었음)"; fi
if (( COMMIT )); then
  idargs=()
  git config user.name  >/dev/null || idargs+=(-c "user.name=candidate")
  git config user.email >/dev/null || idargs+=(-c "user.email=candidate@localhost")
  paths=(); for p in AGENTS.md AGENTS.harness.md .gitignore .gitattributes .codex .harness .agents docs ctx; do [[ -e "$p" ]] && paths+=("$p"); done
  git add -- "${paths[@]}"
  if ! git diff --cached --quiet; then
    git ${idargs[@]+"${idargs[@]}"} commit -q -m "chore(harness): install hynix harness (AGENTS.md, skills, subagents, hooks, rules, ctx)"
    say "커밋: $(git log --oneline -1)"
  fi
fi

say "설치 ${#copied[@]}개, 기존 파일이라 건너뜀 ${#skipped[@]}개"
(( ${#skipped[@]} )) && printf '   skip: %s\n' "${skipped[@]}" | head -20
echo
"$WS/.harness/bin/doctor.sh" || true
cat <<EOF

다음 단계
  1. 과제 시작 직후:  .harness/bin/clock.sh start
  2. codex 실행 → 폴더 신뢰 승인 → /hooks 에서 하네스 훅 신뢰 → /model 로 Astra 아닌 모델 확인
  3. 첫 요청:  \$capture-requirements README를 읽고 요구사항 원장을 만들어줘
EOF
