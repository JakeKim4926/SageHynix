#!/usr/bin/env python3
"""Codex hook entrypoint for the hackathon harness.

Usage (from .codex/hooks.json):
    harness_hook.py session-start   # SessionStart: inject handoff reminder + ctx/ list
    harness_hook.py prompt          # UserPromptSubmit: model guard + related ctx/ entries, log prompt
    harness_hook.py pretool         # PreToolUse: block outbound / destructive / self-edit

Reads one JSON object on stdin. Standard library only.
Fails open (exit 0, no output) on internal errors so a broken hook never wedges a session,
except that PreToolUse denials are always explicit JSON.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

STATE_DIR = Path(os.environ.get("HYNIX_HARNESS_HOME", Path(__file__).resolve().parents[2] / ".harness" / "state"))
WORKSPACE_FILE = STATE_DIR / "workspace"

LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1")


# ---------------------------------------------------------------- utilities

def workspace_root(cwd: str) -> Path:
    if WORKSPACE_FILE.exists():
        ws = WORKSPACE_FILE.read_text(encoding="utf-8").strip()
        if ws:
            return Path(ws)
    p = Path(cwd or ".").resolve()
    for cand in [p, *p.parents]:
        if (cand / ".git").exists():
            return cand
    return p


def log_event(cwd: str, name: str, record: dict) -> None:
    if os.environ.get("HYNIX_HARNESS_NOLOG"):  # self-tests from doctor.sh
        return
    try:
        log_dir = workspace_root(cwd) / ".harness" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
        with open(log_dir / f"{name}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------- ctx/ work memory
# Reads ctx/index.jsonl directly (no import of ctx.py, no file hashing) so the hook stays fast
# and self-contained. Statuses shown here are as recorded; `ctx.py get` checks freshness.

CTX_TOKEN = re.compile(r"[0-9a-z가-힣_]{2,}")


def ctx_entries(cwd: str) -> dict:
    entries = {}
    try:
        lines = (workspace_root(cwd) / "ctx" / "index.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        return entries
    for line in lines:
        try:
            ev = json.loads(line)
            entries.setdefault(ev["id"], {"id": ev["id"]}).update(
                {k: v for k, v in ev.items() if k in ("q", "summary", "status", "tags", "serves")})
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return entries


def ctx_line(e: dict) -> str:
    return f"{e['id']} [{e.get('status', 'draft')}] {(e.get('summary') or e.get('q', ''))[:80]}"


def ctx_brief(cwd: str, limit: int = 25) -> str:
    entries = [e for e in ctx_entries(cwd).values() if e.get("status") != "superseded"]
    if not entries:
        return ""
    lines = [f"[ctx] 작업 기억 {len(entries)}개 (ctx/INDEX.md). 조사·분석 전 `python3 .harness/bin/ctx.py find <키워드>`; "
             "valid 항목은 `ctx.py get <ID>`로 읽고 재사용 — 같은 조사·질문을 다시 하지 말 것."]
    lines += [f"  - {ctx_line(e)}" for e in entries[-limit:]]
    if len(entries) > limit:
        lines.append(f"  - … 외 {len(entries) - limit}개는 ctx/INDEX.md")
    return "\n".join(lines)


def ctx_related(cwd: str, prompt: str, limit: int = 3) -> str:
    q = prompt.lower()
    ranked = []
    for e in ctx_entries(cwd).values():
        if e.get("status") == "superseded":
            continue
        hay = " ".join([e["id"].replace("/", " "), e.get("q", ""), e.get("summary", ""),
                        " ".join(e.get("tags", []))]).lower()
        s = max(sum(1 for t in set(CTX_TOKEN.findall(q)) if t in hay),
                sum(1 for t in set(CTX_TOKEN.findall(hay)) if t in q))
        s += 5 if e["id"].lower() in q else 0
        if s >= 2:
            ranked.append((s, e))
    if not ranked:
        return ""
    ranked.sort(key=lambda r: -r[0])
    return "[ctx] 관련 기록 — 재사용 전 `ctx.py get <ID>`로 신선도 확인: " + \
        " / ".join(ctx_line(e) for _, e in ranked[:limit])


def emit_context(event: str, text: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}},
                     ensure_ascii=False))


def deny(cwd: str, reason: str, detail: str) -> None:
    log_event(cwd, "guard", {"decision": "deny", "reason": reason, "detail": detail[:300]})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"[harness guard] {reason}",
    }}, ensure_ascii=False))


# ---------------------------------------------------------------- PreToolUse policy

PROTECTED_PATH = re.compile(r"(\.codex/config\.toml|/etc/codex|\.codex/hooks|\.codex/hooks\.json|\.codex/rules|\.codex/auth\.json)")
WRITE_VERBS = re.compile(r"(>|\btee\b|\bsed\s+-i|\bcp\b|\bmv\b|\brm\b|\bchmod\b|\btruncate\b|\bperl\s+-pi)")
CTX_EVENTS = re.compile(r"ctx/index\.jsonl")
CTX_EVENTS_REASON = "ctx/index.jsonl은 직접 수정 금지. `python3 .harness/bin/ctx.py new|done|status`로만 기록."


def _urls(cmd: str):
    return re.findall(r"https?://([^/\s'\"]+)", cmd)


def check_shell(cmd: str):
    """Return a deny reason for a shell command, or None to allow."""
    c = " ".join(cmd.split())

    if re.search(r"\bgit\b(\s+-\S+(\s+\S+)?)*\s+push\b", c):
        return "git push는 금지(외부 전송). 결과는 작업 공간에 저장만 한다."
    if re.search(r"(^|[;&|]\s*|\s)(scp|sftp|ssh|nc|ncat|netcat|socat|telnet|ftp)\s", c + " "):
        return "원격 접속/전송 도구(scp/ssh/nc 등)는 금지."
    if re.search(r"\brsync\b.*\s\S+:\S*", c):
        return "원격 rsync는 금지."

    # Outbound uploads: data/form/upload flags towards a non-local host.
    if re.search(r"\b(curl|wget|http|https|xh)\b", c):
        upload = re.search(r"(\s-T\s|--upload-file|\s-F\s|--form\b|\s-d\s|--data\S*|\s-X\s*(POST|PUT|PATCH)|--post-(data|file)|--method=(POST|PUT|PATCH))", c + " ")
        hosts = _urls(c)
        remote = [h for h in hosts if h.split(":")[0].strip("[]") not in {x.strip("[]") for x in LOCAL_HOSTS}]
        if upload and remote:
            return f"외부 호스트({remote[0]})로의 업로드/POST는 금지. 로컬 서버 테스트는 localhost/0.0.0.0만."

    # Secrets and platform credentials.
    if re.search(r"\.codex/auth\.json", c) or re.search(r"(^|[;&|]\s*)(printenv|env)\s*($|[;&|])", c):
        return "키·토큰·환경변수 출력은 금지."
    if re.search(r"echo\s+\S*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD)\w*", c, re.I):
        return "키·토큰 값 출력은 금지."

    # Platform settings and the harness guardrails themselves.
    if PROTECTED_PATH.search(c) and WRITE_VERBS.search(c):
        return "플랫폼 Codex 설정·하네스 가드레일(.codex/hooks, .codex/rules) 수정은 금지. 필요하면 사용자에게 요청."
    if CTX_EVENTS.search(c) and WRITE_VERBS.search(c):
        return CTX_EVENTS_REASON

    # Platform / supervisor processes.
    if re.search(r"\bkill\s+(-\S+\s+)*-1\b|\bkill\s+(-\S+\s+)*1\b(?!\d)", c) or \
       re.search(r"\b(pkill|killall)\b.*\b(codex|e2b|envd|proctor|cofa|probe|node\s*$)", c, re.I) or \
       re.search(r"\bkillall\s*$", c):
        return "플랫폼·감독 프로세스 종료는 금지. 본인이 띄운 서버만 PID/이름으로 종료."

    # Destructive operations that would erase work or history.
    if re.search(r"\brm\s+(-\S*[rR]\S*\s+)+(-\S+\s+)*(/|~|\$HOME|\.|\.\.|\*|\.git)(\s|/?$|/\*)", c + " "):
        return "작업 공간/히스토리 대량 삭제는 금지. 지울 파일을 명시해서 다시 요청."
    if re.search(r"\bgit\s+(reset\s+--hard|clean\s+-\S*f|checkout\s+--\s+\.|restore\s+\.|push\s+--force|filter-branch|rebase\b)", c):
        return "작업 손실·히스토리 재작성 git 명령은 금지(git log도 평가 대상). 사용자가 직접 판단해서 실행."
    return None


def check_patch(patch: str, cwd: str):
    ws = workspace_root(cwd)
    for path in re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, re.M):
        p = path.strip().replace("\\", "/")
        if PROTECTED_PATH.search(p):
            return f"{p}: 하네스 가드레일/플랫폼 설정 파일은 에이전트가 수정할 수 없음."
        if CTX_EVENTS.search(p):
            return CTX_EVENTS_REASON
        if p.startswith("/") or p.startswith("~"):
            target = Path(os.path.expanduser(p)).resolve()
            try:
                target.relative_to(ws.resolve())
            except ValueError:
                if not str(target).startswith(str(Path.home() / "wt")):
                    return f"{p}: 작업 공간 밖 파일 수정은 금지."
    return None


def handle_pretool(payload: dict) -> None:
    cwd = payload.get("cwd", "")
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input") or {}
    cmd = tin.get("command", "") if isinstance(tin, dict) else str(tin)
    if isinstance(cmd, list):
        cmd = " ".join(map(str, cmd))
    if tool == "apply_patch" or cmd.lstrip().startswith("*** Begin Patch"):
        reason = check_patch(cmd, cwd)
    else:
        reason = check_shell(cmd)
    if reason:
        deny(cwd, reason, cmd)


# ---------------------------------------------------------------- other events

def handle_prompt(payload: dict) -> None:
    cwd = payload.get("cwd", "")
    model = str(payload.get("model") or "")
    log_event(cwd, "prompts", {"model": model, "prompt": str(payload.get("prompt", ""))[:2000]})
    if "astra" in model.lower():
        print(json.dumps({"decision": "block",
                          "reason": f"[harness] 현재 모델 '{model}'은 Astra 계열(대회 사용 제한). "
                                    "/model 에서 Sol 6.1 / Terra 5.6 / Luna 6 / Sol 6.0 중 하나로 바꾼 뒤 다시 요청하세요."},
                         ensure_ascii=False))
        return
    related = ctx_related(cwd, str(payload.get("prompt", "")))
    if related:
        emit_context("UserPromptSubmit", related)


def handle_session_start(payload: dict) -> None:
    cwd = payload.get("cwd", "")
    lines = []
    worklog = workspace_root(cwd) / "docs" / "WORKLOG.md"
    if payload.get("source") in ("resume", "compact", "clear", "fork") or (worklog.exists() and worklog.stat().st_size > 400):
        lines.append("[harness] 이어서 작업 중이면 먼저 docs/WORKLOG.md 의 '현재 상태/다음 단계'를 읽고 시작할 것.")
    model = str(payload.get("model") or "")
    if "astra" in model.lower():
        lines.append(f"[harness] ⚠ 현재 모델 '{model}'은 Astra 계열(사용 제한). /model 로 변경 필요.")
    brief = ctx_brief(cwd)
    if brief:
        lines.append(brief)
    if lines:
        emit_context("SessionStart", "\n".join(lines))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    try:
        if mode == "pretool":
            handle_pretool(payload)
        elif mode == "prompt":
            handle_prompt(payload)
        elif mode == "session-start":
            handle_session_start(payload)
    except Exception as exc:  # fail open, but leave a trace
        log_event(payload.get("cwd", ""), "hook-errors", {"mode": mode, "error": repr(exc)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
