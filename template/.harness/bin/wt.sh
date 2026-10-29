#!/usr/bin/env bash
# Parallel implementation lanes with git worktree.
#   wt.sh new <lane> [base]   create ~/wt/<lane> on branch lane/<lane>
#   wt.sh list                list worktrees
#   wt.sh merge <lane>        merge lane/<lane> into the current branch (no-ff)
#   wt.sh rm <lane>           remove worktree and branch
# Worktrees live outside the workspace so they are not submitted twice;
# only what you merge back ends up in the submission.
set -euo pipefail
WT_ROOT="${WT_ROOT:-$HOME/wt}"
cmd="${1:-list}"; lane="${2:-}"
root="$(git rev-parse --show-toplevel)"

need_lane() { [[ -n "$lane" ]] || { echo "lane 이름 필요"; exit 2; }; }

case "$cmd" in
  new)
    need_lane
    base="${3:-HEAD}"
    if [[ -n "$(git -C "$root" status --porcelain -- AGENTS.md .codex .agents)" ]]; then
      echo "하네스 파일에 커밋 안 된 변경이 있습니다. 먼저 커밋해야 레인에도 반영됩니다."; exit 1
    fi
    mkdir -p "$WT_ROOT"
    git -C "$root" worktree add -b "lane/$lane" "$WT_ROOT/$lane" "$base"
    echo
    echo "새 터미널 탭에서:  cd $WT_ROOT/$lane && codex"
    echo "레인 규칙: 이 레인의 범위 밖 파일은 건드리지 않기. 끝나면 커밋 후 메인에서 wt.sh merge $lane"
    ;;
  list)
    git -C "$root" worktree list
    ;;
  merge)
    need_lane
    if [[ -n "$(git -C "$root" status --porcelain --untracked-files=no)" ]]; then
      echo "메인 작업 공간에 커밋 안 된 변경이 있습니다. 먼저 커밋하세요."; exit 1
    fi
    if [[ -d "$WT_ROOT/$lane" && -n "$(git -C "$WT_ROOT/$lane" status --porcelain --untracked-files=no)" ]]; then
      echo "레인 $lane 에 커밋 안 된 변경이 있습니다."; exit 1
    fi
    git -C "$root" merge --no-ff "lane/$lane" -m "merge(lane): $lane"
    echo "병합 완료. 테스트 재실행: .harness/bin/verify.sh"
    ;;
  rm)
    need_lane
    git -C "$root" worktree remove "$WT_ROOT/$lane"
    git -C "$root" branch -d "lane/$lane"
    ;;
  *) sed -n '2,9p' "$0"; exit 2 ;;
esac
