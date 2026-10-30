#!/usr/bin/env bash
# Self-test for the harness repo: hook policy, rules, skill frontmatter, 6-section SCRIPT format
# in prompts and agents, JSON/TOML syntax, shell syntax, and an end-to-end bootstrap.
set -uo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"
PY="$(command -v python3 || command -v python)"
fail=0
step() { printf '\n== %s\n' "$*"; }
check() { if "$@"; then echo "  ok"; else echo "  FAIL: $*"; fail=1; fi; }

step "hook policy unit tests"
check "$PY" -m unittest discover -s tests -q

step "JSON / TOML syntax"
check "$PY" - <<'EOF'
import json, sys, pathlib
try:
    import tomllib
except ImportError:
    tomllib = None
root = pathlib.Path(".")
for p in [*root.glob("template/.codex/*.json"), *root.glob(".agents/plugins/*.json"), *root.glob("plugins/*/.codex-plugin/*.json")]:
    json.loads(p.read_text(encoding="utf-8"))
if tomllib:
    for p in [*root.glob("template/.codex/*.toml"), *root.glob("template/.codex/agents/*.toml")]:
        d = tomllib.loads(p.read_text(encoding="utf-8"))
        if "agents/" in p.as_posix():
            missing = {"name", "description", "developer_instructions"} - d.keys()
            assert not missing, f"{p}: missing {missing}"
EOF

step "skills: exactly research, verify, doc; name matches folder; description present"
check "$PY" - <<'EOF'
import re, pathlib
skills = sorted(pathlib.Path("plugins/hynix-harness/skills").glob("*/SKILL.md"))
assert [p.parent.name for p in skills] == ["doc", "research", "verify"], [p.parent.name for p in skills]
for p in skills:
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    assert m, f"{p}: no frontmatter"
    fm = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    assert fm.get("name", "").strip() == p.parent.name, f"{p}: name != folder"
    assert len(fm.get("description", "").strip()) > 40, f"{p}: description too short"
EOF

step "SCRIPT: every copyable script uses the 6 sections in order; agents name them"
check "$PY" - <<'EOF'
import re, pathlib
secs = ["[Role]", "[Context]", "[Task]", "[Rules]", "[Output]", "[Done]"]
t = pathlib.Path("template/prompts/SCRIPT.md").read_text(encoding="utf-8")
blocks = re.findall(r"### S\d.*?\n```\n(.*?)```", t, re.S)
assert len(blocks) >= 6, f"expected >=6 scripts, got {len(blocks)}"
for b in blocks:
    got = [l[:l.index("]") + 1] for l in b.splitlines() if l.startswith("[")]
    assert got == secs, f"sections out of order: {got}"
for p in pathlib.Path("template/.codex/agents").glob("*.toml"):
    a = p.read_text(encoding="utf-8")
    assert "SCRIPT" in a and all(s in a for s in ["[Role]", "[Rules]", "[Output]", "[Done]"]), p
EOF

step "no references to removed parts"
if grep -rnE 'ctx\.py|clock\.sh|fanout|wt\.sh|\$(task-intake|stakeholder-sync|parallel-research|data-profile|plan-slice|worktree-lanes|verify-gate|doc-writer|doc-review|cognition-check|defense-prep|handoff|ctx)\b|INTENT\.md|PLAN\.md|WORKLOG\.md|COGNITION\.md|DECISIONS\.md' \
     template plugins bootstrap.sh; then echo "  FAIL: stale references above"; fail=1; else echo "  ok"; fi

step "shell syntax"
for f in bootstrap.sh template/.harness/bin/*.sh tests/run_all.sh; do check bash -n "$f"; done

step "execpolicy rules"
if command -v codex >/dev/null; then
  for c in "git push origin main:forbidden" "scp a b:/c:forbidden" "git reset --hard:prompt" "git status:allow"; do
    cmd="${c%:*}"; want="${c##*:}"
    # shellcheck disable=SC2086
    got="$(codex execpolicy check --rules template/.codex/rules/harness.rules -- $cmd 2>/dev/null)"
    if [[ "$got" == *"\"$want\""* ]]; then echo "  ok: $cmd → $want"; else echo "  FAIL: $cmd → $got"; fail=1; fi
  done
else echo "  skip: codex not installed"; fi

step "bootstrap into a temp workspace"
tmp="$(mktemp -d)"
export HYNIX_HARNESS_HOME="$tmp/state"
mkdir -p "$tmp/ws"
if bash bootstrap.sh "$tmp/ws" >"$tmp/boot.log" 2>&1 && ! grep -q "FAIL" "$tmp/boot.log" \
   && [[ -f "$tmp/ws/AGENTS.md" && -f "$tmp/ws/.agents/skills/verify/SKILL.md" && -f "$tmp/ws/prompts/SCRIPT.md" ]] \
   && [[ "$(ls "$tmp/ws/.agents/skills" | wc -l)" -eq 3 ]] \
   && [[ "$(git -C "$tmp/ws" log --oneline | wc -l)" -eq 1 ]]; then
  bash bootstrap.sh "$tmp/ws" >/dev/null 2>&1
  if [[ "$(git -C "$tmp/ws" log --oneline | wc -l)" -eq 1 ]]; then echo "  ok (installed, idempotent)"
  else echo "  FAIL: re-run created a new commit"; fail=1; fi
else echo "  FAIL: see $tmp/boot.log"; fail=1; fi

echo; if (( fail )); then echo "SOME CHECKS FAILED"; else echo "ALL CHECKS PASSED"; fi
exit $fail
