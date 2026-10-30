#!/usr/bin/env python3
"""Intent trace gate: docs/task/ (원문) · docs/INTENT.md (계약) · docs/ledger.jsonl (이력).

Usage:
    intent_trace.py pre-commit          # git pre-commit (.codex/hooks/git/pre-commit)
    intent_trace.py commit-msg <file>   # git commit-msg (.codex/hooks/git/commit-msg)
    intent_trace.py report              # 추적표: AC | R | 원문 근거 | 결정 | 최신 검증

[harness guard] = 멈추고 사용자에게 보고. [trace check] = 메시지대로 고쳐 다시 커밋.
INTENT·ledger 검사는 해당 파일이 생기기 전(하네스 유지보수·과제 반입 단계)에는 하지 않는다.
Standard library only. Self-test: python3 -m unittest discover -s .codex/hooks -p "test_*.py"
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TASK_DIR = "docs/task/"
INTENT = "docs/INTENT.md"
LEDGER = "docs/ledger.jsonl"

AC_ROW = re.compile(r"^\|\s*(AC-\d+\.\d+)\s*\|")      # 표 첫 칸이 AC-n.m인 행만 계약으로 본다
R_ID = re.compile(r"\bR-\d+\b")
SOURCE = re.compile(r"docs/task/[^\s|]+?:\d+|\bA-\d+\b")  # 원문 줄 근거 또는 가정
REQUIRED = {
    "decision": ("id", "refs", "what", "why", "by"),
    "assumption": ("id", "refs", "what"),
    "question": ("id", "refs", "what"),
    "answer": ("refs", "what"),
    "verify": ("refs", "result", "line"),
}
ID_PREFIX = {"decision": "D", "assumption": "A", "question": "Q"}
VERIFY_RESULTS = ("PASS", "FAIL", "미검증", "생략")
GUARD, CHECK = "[harness guard]", "[trace check]"


# ---------------------------------------------------------------- parsing

def git_blob(spec: str):
    """`HEAD:path` or `:path` (index). None if absent."""
    r = subprocess.run(["git", "show", spec], capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def parse_ledger(text: str):
    """Return (events, errors). Each event gets `_line` (1-based)."""
    events, errors, seen = [], [], set()
    for n, raw in enumerate((text or "").splitlines(), 1):
        if not raw.strip():
            continue
        where = f"{LEDGER}:{n}"
        try:
            e = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{CHECK} {where} JSON 오류 — {exc.msg} (열 {exc.colno}). 한 줄에 객체 하나, 큰따옴표만.")
            continue
        if not isinstance(e, dict) or e.get("type") not in REQUIRED:
            errors.append(f"{CHECK} {where} type은 {'/'.join(REQUIRED)} 중 하나.")
            continue
        kind = e["type"]
        missing = [k for k in REQUIRED[kind] if not e.get(k)]
        if missing:
            errors.append(f"{CHECK} {where} {kind}에 {', '.join(missing)} 없음.")
        if not isinstance(e.get("refs"), list):
            errors.append(f"{CHECK} {where} refs는 목록이어야 함 (예: [\"AC-1.1\"]).")
            e["refs"] = []
        prefix = ID_PREFIX.get(kind)
        if prefix and e.get("id"):
            if not re.fullmatch(prefix + r"-\d+", str(e["id"])):
                errors.append(f"{CHECK} {where} {kind} id는 {prefix}-n 형식.")
            elif e["id"] in seen:
                errors.append(f"{CHECK} {where} id {e['id']} 중복 — 다음 번호를 쓴다.")
            seen.add(e["id"])
        if kind == "verify" and e.get("result") not in VERIFY_RESULTS:
            errors.append(f"{CHECK} {where} verify result는 {'/'.join(VERIFY_RESULTS)} 중 하나.")
        e["_line"] = n
        events.append(e)
    return events, errors


def ac_rows(text: str):
    """{AC id: 공백 정규화한 표 행}. 중복 AC는 errors로."""
    rows, errors = {}, []
    for line in (text or "").splitlines():
        m = AC_ROW.match(line.strip())
        if not m:
            continue
        if m.group(1) in rows:
            errors.append(f"{CHECK} {INTENT}: {m.group(1)} 행이 둘 이상 — 한 AC는 한 행.")
        rows[m.group(1)] = " ".join(line.split())
    return rows, errors


def covers(event: dict, ac: str) -> bool:
    """refs가 AC 자신이나 부모 R을 가리키면 그 AC를 다룬다 (AC-2.1 ← R-2)."""
    parent = "R-" + ac.split("-")[1].split(".")[0]
    return ac in event.get("refs", []) or parent in event.get("refs", [])


def latest_verify(events, ac: str):
    hits = [e for e in events if e["type"] == "verify" and covers(e, ac)]
    return hits[-1] if hits else None


# ---------------------------------------------------------------- git hooks

def pre_commit() -> list:
    problems = []

    # 1. 원문은 반입(추가)만 허용
    r = subprocess.run(["git", "diff", "--cached", "--name-status", "--no-renames", "--", TASK_DIR],
                       capture_output=True, text=True, encoding="utf-8")
    for row in r.stdout.splitlines():
        status, _, path = row.partition("\t")
        if status[:1] in ("M", "D", "T"):
            problems.append(f"{GUARD} {path}: 원문은 반입 후 수정·삭제 금지. 멈추고 사용자에게 보고한다"
                            f" (되돌리기: git restore --staged --worktree -- {path}).")

    # 2. ledger는 추가만, 줄마다 스키마 확인
    head_ledger = git_blob("HEAD:" + LEDGER) or ""
    staged_ledger = git_blob(":" + LEDGER)
    if staged_ledger is None:
        staged_ledger = ""
        if head_ledger:
            problems.append(f"{CHECK} {LEDGER} 삭제 금지 — git restore --staged --worktree -- {LEDGER}")
    elif not staged_ledger.startswith(head_ledger):
        old, new = head_ledger.splitlines(), staged_ledger.splitlines()
        first = next((i + 1 for i, line in enumerate(old) if i >= len(new) or new[i] != line), len(old))
        problems.append(f"{CHECK} {LEDGER}:{first} 기존 줄 수정·삭제 금지 — 기존 줄은 HEAD 그대로 두고"
                        f" 정정은 끝에 새 줄로 (git show HEAD:{LEDGER} 로 원래 내용 확인).")
    events, errors = parse_ledger(staged_ledger)
    problems += errors

    # 3. 계약: AC 행마다 원문 근거, 바뀐 AC에는 같은 커밋의 decision
    staged_intent = git_blob(":" + INTENT)
    head_intent = git_blob("HEAD:" + INTENT)
    if staged_intent is not None:
        rows, errors = ac_rows(staged_intent)
        problems += errors
        for ac, row in rows.items():
            if not SOURCE.search(row):
                problems.append(f"{CHECK} {INTENT}: {ac} 행에 원문 근거(docs/task/<파일>:<줄>) 또는 가정 A-n이 없음.")
    if head_intent is not None:
        before, _ = ac_rows(head_intent)
        after, _ = ac_rows(staged_intent or "")
        new_events = [e for e in events if e["_line"] > len(head_ledger.splitlines())]
        for ac in sorted(a for a, row in before.items() if after.get(a) != row):
            if not any(e["type"] == "decision" and covers(e, ac) for e in new_events):
                problems.append(
                    f"{GUARD} {ac} 변경·삭제에 이번 커밋의 decision이 없음. 의도 변경은 사용자 승인이 필요하다 — "
                    f"승인 전이면 멈추고 변경 전/후를 보여 승인을 요청. 승인받았으면 ledger 끝에 "
                    f'{{"type":"decision","id":"D-n","refs":["{ac}"],"what":"전→후","why":"원문 근거","by":"user"}}'
                    f" 추가 → git add {LEDGER} → 다시 커밋.")
    return problems


def commit_msg(msg_file: str) -> list:
    text = Path(msg_file).read_text(encoding="utf-8", errors="replace")
    subject = next((ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")), "")
    if not re.match(r"(feat|fix)[(:!]", subject) or git_blob(":" + INTENT) is None:
        return []
    rids = sorted(set(R_ID.findall(subject)))
    if not rids:
        return [f"{CHECK} feat·fix 제목에 R-n 필요 (예: feat(etl): 결측 ID 제거 — R-2 수율 왜곡 방지)."]
    events, _ = parse_ledger(git_blob(":" + LEDGER) or "")
    new_events = [e for e in events if e["_line"] > len((git_blob("HEAD:" + LEDGER) or "").splitlines())]
    rows, _ = ac_rows(git_blob(":" + INTENT) or "")
    problems = []
    for rid in rids:
        acs = [ac for ac in rows if ac.startswith("AC-" + rid[2:] + ".")]
        if not acs:
            problems.append(f"{CHECK} {rid}: {INTENT}에 AC-{rid[2:]}.n 행이 없음 — $intent로 수용 기준부터.")
            continue
        results = {ac: (latest_verify(events, ac) or {}).get("result") for ac in acs}
        failed = [ac for ac, res in results.items() if res == "FAIL"]
        # 이전 커밋의 PASS는 지금 변경을 검증하지 않는다: 이번 커밋에 추가한 PASS만 인정
        fresh = [ac for ac in acs if (latest_verify(new_events, ac) or {}).get("result") == "PASS"]
        if failed or not fresh:
            state = f"최신 FAIL: {', '.join(failed)}" if failed else "이번 커밋에서 추가한 verify PASS 없음"
            problems.append(f"{CHECK} {rid}: 스테이징된 {LEDGER}에 {state}. $verify 4단계로 "
                            f'{{"type":"verify","refs":["AC-…"],"result":"PASS","line":"…"}} 추가 → '
                            f"git add {LEDGER} → 다시 커밋. FAIL이면 고친 뒤 다시 검증한다.")
    return problems


# ---------------------------------------------------------------- report

def summary(root: Path):
    """SessionStart용 한 줄. INTENT가 없으면 None."""
    intent = root / INTENT
    if not intent.exists():
        return None
    ledger = root / LEDGER
    events, errors = parse_ledger(ledger.read_text(encoding="utf-8") if ledger.exists() else "")
    rows, _ = ac_rows(intent.read_text(encoding="utf-8"))
    passed = sum(1 for ac in rows if (latest_verify(events, ac) or {}).get("result") == "PASS")
    answered = {r for e in events if e["type"] == "answer" for r in e["refs"]}
    open_q = [e["id"] for e in events if e["type"] == "question" and e.get("id") not in answered]
    line = f"AC {len(rows)}개 · 최신 PASS {passed}개 · 열린 질문 {len(open_q)}개{' (' + ', '.join(open_q) + ')' if open_q else ''}"
    return line + (f" · ledger 오류 {len(errors)}건" if errors else "")


def report(root: Path) -> int:
    intent = root / INTENT
    if not intent.exists():
        print(f"{INTENT} 없음 — $intent로 원문 반입·계약부터.")
        return 0
    ledger = root / LEDGER
    events, errors = parse_ledger(ledger.read_text(encoding="utf-8") if ledger.exists() else "")
    rows, _ = ac_rows(intent.read_text(encoding="utf-8"))
    print("| AC | R | 원문 근거 (왜) | 결정 D (목적 변경) | 최신 검증 (달성) |")
    print("|---|---|---|---|---|")
    for ac, row in rows.items():
        decisions = [e["id"] for e in events if e["type"] == "decision" and covers(e, ac)]
        v = latest_verify(events, ac)
        print(f"| {ac} | {', '.join(sorted(set(R_ID.findall(row)))) or '-'} | {', '.join(SOURCE.findall(row)) or '없음'} "
              f"| {', '.join(decisions) or '-'} | {v['result'] + ' ' + v['line'] if v else '미검증'} |")
    answered = {r for e in events if e["type"] == "answer" for r in e["refs"]}
    for e in events:
        if e["type"] == "question" and e.get("id") not in answered:
            print(f"열린 질문 {e['id']}: {e.get('what')}")
        if e["type"] == "assumption":
            print(f"가정 {e['id']}: {e.get('what')}")
    for err in errors:
        print(err)
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    root = Path(top.stdout.strip()) if top.returncode == 0 else Path.cwd()
    os.chdir(root)
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "report":
        return report(root)
    if mode == "pre-commit":
        problems = pre_commit()
    elif mode == "commit-msg" and len(sys.argv) > 2:
        problems = commit_msg(sys.argv[2])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    for p in problems:
        print(p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
