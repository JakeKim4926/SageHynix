#!/usr/bin/env bash
# Self-test for the harness repo: hook policy, rules, skill frontmatter, JSON/TOML syntax,
# shell syntax, and an end-to-end bootstrap into a temporary workspace.
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

step "skill frontmatter (name matches folder, description present)"
check "$PY" - <<'EOF'
import re, pathlib
for p in pathlib.Path("plugins/hynix-harness/skills").glob("*/SKILL.md"):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    assert m, f"{p}: no frontmatter"
    fm = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    assert fm.get("name", "").strip() == p.parent.name, f"{p}: name != folder"
    assert len(fm.get("description", "").strip()) > 40, f"{p}: description too short"
EOF

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
   && [[ -f "$tmp/ws/AGENTS.md" && -f "$tmp/ws/.agents/skills/verify-gate/SKILL.md" ]] \
   && [[ "$(git -C "$tmp/ws" log --oneline | wc -l)" -eq 1 ]]; then
  bash bootstrap.sh "$tmp/ws" >/dev/null 2>&1
  if [[ "$(git -C "$tmp/ws" log --oneline | wc -l)" -eq 1 ]]; then echo "  ok (installed, idempotent)"
  else echo "  FAIL: re-run created a new commit"; fail=1; fi
  if git -C "$tmp/ws" ls-files --error-unmatch ctx/README.md ctx/index.jsonl .gitattributes >/dev/null 2>&1 \
     && [[ -f "$tmp/ws/ctx/INDEX.md" ]] && ! git -C "$tmp/ws" ls-files --error-unmatch ctx/INDEX.md >/dev/null 2>&1 \
     && [[ "$(git -C "$tmp/ws" check-attr merge ctx/index.jsonl)" == *union ]]; then echo "  ok (ctx/ committed, INDEX.md generated, union merge)"
  else echo "  FAIL: ctx/ install"; fail=1; fi
else echo "  FAIL: see $tmp/boot.log"; fail=1; fi

step "fanout reuses valid ctx lanes (fake codex)"
cat > "$tmp/fakecodex" <<'EOF'
#!/usr/bin/env bash
out=""; while (( $# )); do [[ "$1" == -o ]] && { out="$2"; shift; }; shift; done
printf '## 결론\n- fake 결론\n## 근거\n- [사실] x\n## 미확인\n없음\n' > "$out"
echo run >> "$(dirname "$out")/../../../.fake-runs"
EOF
chmod +x "$tmp/fakecodex"
mkdir -p "$tmp/ws/ctx/research"
printf 'alpha|첫 질문\nbeta|두 번째 질문\n# gamma|주석\n' > "$tmp/ws/ctx/research/lanes.txt"
runs() { if [[ -f "$tmp/ws/.fake-runs" ]]; then wc -l < "$tmp/ws/.fake-runs" | tr -d ' '; else echo 0; fi; }
fan() { (cd "$tmp/ws" && CODEX_BIN="$tmp/fakecodex" bash .harness/bin/fanout.sh ctx/research/lanes.txt 2) >"$tmp/fan.log" 2>&1; }
fan; first=$(runs)
fan; second=$(runs)
FANOUT_FORCE=1 fan; third=$(runs)
state=$(cd "$tmp/ws" && "$PY" .harness/bin/ctx.py state research/alpha)
if [[ "$first" == 2 && "$second" == 2 && "$third" == 4 && "$state" == valid ]]; then echo "  ok (2 lanes run, re-run skipped, FANOUT_FORCE re-ran)"
else echo "  FAIL: runs $first/$second/$third, state=$state (see $tmp/fan.log)"; fail=1; fi

echo; if (( fail )); then echo "SOME CHECKS FAILED"; else echo "ALL CHECKS PASSED"; fi
exit $fail
