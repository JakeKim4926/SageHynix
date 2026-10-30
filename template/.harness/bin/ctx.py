#!/usr/bin/env python3
"""Work memory for the harness: the ctx/ master folder.

    ctx.py init
    ctx.py find [WORDS...]                 search before working; reuse what is valid
    ctx.py get ID [--all]                  freshness + metadata + main file
    ctx.py new KIND SLUG --q TEXT [--serves R-1,R-2] [--inputs F ...] [--uses ID ...] [--tags a,b] [--redo]
    ctx.py done ID [--summary TEXT] [--inputs F ...]
    ctx.py status ID draft|valid|stale|superseded [--by ID] [--note TEXT]
    ctx.py state ID                        print effective status only (for scripts)
    ctx.py check                           recompute freshness, rewrite INDEX.md
    ctx.py index                           rewrite INDEX.md

ID is KIND/SLUG (e.g. research/anomaly); each entry is the folder ctx/KIND/SLUG/.
Metadata lives only in ctx/index.jsonl: append-only events written by this script.
The model writes the Markdown bodies; `done` refuses bodies with empty required sections.
An entry goes stale when an input file changes or an entry it uses is redone or not valid.
Standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path


def _root() -> Path:
    if os.environ.get("CTX_ROOT"):
        return Path(os.environ["CTX_ROOT"]).resolve()
    here = Path(__file__).resolve().parents[2]  # <ws>/.harness/bin/ctx.py
    return here if (here / ".harness").is_dir() else Path.cwd().resolve()


ROOT = _root()
CTX = ROOT / "ctx"
EVENTS = CTX / "index.jsonl"
INDEX_MD = CTX / "INDEX.md"
SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]{0,47}$")
TOKEN = re.compile(r"[0-9a-z가-힣_]{2,}")
STATUSES = ("draft", "valid", "stale", "superseded")

# kind -> main file, section the one-line summary comes from, body templates, required sections.
# A required list of [] means "the file must have content beyond template comments".
KINDS = {
    "research": {
        "main": "report.md", "summary": "결론",
        "files": {
            "brief.md": "# {id} — 조사 지시서\n\n- 질문: {q}\n- 관련 요구사항: {serves}\n"
                        "- 범위 밖: <!-- 하지 말 것 -->\n- 결과: report.md\n",
            "report.md": "# {id} — 조사 보고\n\n"
                         "## 결론\n<!-- 3줄 이내. 첫 줄이 INDEX 한 줄 요약이 된다 -->\n\n"
                         "## 선택지\n<!-- 이름 | 충족 R | 비용 | 위험. 해당 없으면 '없음' -->\n\n"
                         "## 근거\n<!-- 주장마다 [사실|추론] + 출처(명령, 파일:줄, URL) -->\n\n"
                         "## 미확인\n<!-- 확인 못 한 것. 없으면 '없음' -->\n\n"
                         "## 담당자 질문\n",
        },
        "required": {"report.md": ["결론", "근거", "미확인"]},
    },
    "data": {
        "main": "notes.md", "summary": "분석 영향",
        "files": {
            "profile.md": "<!-- python3 .agents/skills/data-profile/scripts/profile_data.py <파일> "
                          "> ctx/{id}/profile.md 출력으로 덮어쓴다 -->\n",
            "notes.md": "# {id} — 데이터 메모\n\n"
                        "## 컬럼 의미\n<!-- 컬럼 | 추정 의미 | 근거 | 확신도 -->\n\n"
                        "## 키와 조인\n\n"
                        "## 함정\n<!-- 누수, 시간 순서, 단위 혼재, 중복, 불균형. 없으면 '없음' -->\n\n"
                        "## 분석 영향\n<!-- 그래서 무엇을 조심해서 계산하나. 첫 줄이 한 줄 요약 -->\n",
        },
        "required": {"profile.md": [], "notes.md": ["컬럼 의미", "함정", "분석 영향"]},
    },
    "decision": {
        "main": "decision.md", "summary": "결정",
        "files": {
            "decision.md": "# {id} — 결정\n\n- 관련 요구사항: {serves}\n\n"
                           "## 결정\n<!-- 한 줄 -->\n\n"
                           "## 비교\n<!-- 선택지 × 요구사항 표. 칸마다 근거가 된 ctx ID -->\n\n"
                           "## 버린 대안\n<!-- 대안 — 버린 이유 -->\n\n"
                           "## 근거 대조\n<!-- 결정을 떠받치는 주장 중 원본으로 다시 확인한 것: 명령 → 결과 -->\n\n"
                           "## 남은 위험\n",
        },
        "required": {"decision.md": ["결정", "버린 대안", "근거 대조"]},
    },
    "slice": {
        "main": "slice.md", "summary": "한 일",
        "files": {
            "slice.md": "# {id} — 슬라이스\n\n- 목표: {q}\n- 관련 요구사항: {serves}\n\n"
                        "## 한 일\n\n## 검증\n<!-- 명령 → 결과. 못 한 것은 '미검증' -->\n\n## 남은 것\n",
        },
        "required": {"slice.md": ["한 일", "검증"]},
    },
    "prompt": {
        "main": "prompt.md", "summary": "언제 쓰나",
        "files": {
            "prompt.md": "# {id} — 재사용 프롬프트\n\n## 언제 쓰나\n\n## 프롬프트\n\n"
                         "## 결과 메모\n<!-- 잘 된 점, 고칠 점 -->\n",
        },
        "required": {"prompt.md": ["언제 쓰나", "프롬프트"]},
    },
    "session": {
        "main": "handoff.md", "summary": "다음 단계",
        "files": {
            "handoff.md": "# {id} — 세션 인수인계\n\n## 한 일\n\n## 현재 상태\n\n"
                          "## 다음 단계\n<!-- 바로 실행 가능한 수준으로, 순서대로 -->\n\n"
                          "## 참조한 ctx 항목\n",
        },
        "required": {"handoff.md": ["현재 상태", "다음 단계"]},
    },
    "note": {
        "main": "note.md", "summary": "내용",
        "files": {"note.md": "# {id}\n\n## 내용\n"},
        "required": {"note.md": ["내용"]},
    },
}


# ---------------------------------------------------------------- store

def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def append(event: dict) -> None:
    CTX.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": now(), **event}, ensure_ascii=False) + "\n"
    with open(EVENTS, "a", encoding="utf-8") as f:  # one write per event: safe for parallel lanes
        f.write(line)


def load() -> dict:
    entries = {}
    if not EVENTS.exists():
        return entries
    for n, line in enumerate(EVENTS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            eid = ev["id"]
        except (ValueError, KeyError, TypeError):
            print(f"[ctx] index.jsonl {n}행 손상 — 건너뜀", file=sys.stderr)
            continue
        e = entries.setdefault(eid, {"id": eid, "created": ev.get("ts", "")})
        e.update({k: v for k, v in ev.items() if k not in ("op", "ts")})
        e["updated"] = ev.get("ts", "")
    return entries


def rel(path: str) -> str:
    p = Path(path).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def signature(relpath: str) -> dict:
    p = ROOT / relpath
    st = p.stat()
    return {"size": st.st_size, "mtime": int(st.st_mtime), "sha": sha256(p)}


def freshness(entries: dict, eid: str, seen=frozenset()):
    """Effective (status, reason). Recorded 'valid' degrades to 'stale' on changed inputs/deps."""
    e = entries.get(eid)
    if e is None:
        return "missing", "기록 없음"
    status = e.get("status", "draft")
    if status != "valid":
        return status, e.get("note", "")
    for relpath, sig in (e.get("snap") or {}).items():
        p = ROOT / relpath
        if not p.exists():
            return "stale", f"입력 없음: {relpath}"
        st = p.stat()
        if st.st_size == sig.get("size") and int(st.st_mtime) == sig.get("mtime"):
            continue
        if sha256(p) != sig.get("sha"):
            return "stale", f"입력 변경: {relpath}"
    seen = seen | {eid}
    for dep, version in (e.get("dep_ver") or {}).items():
        if dep in seen:
            continue
        d_status, _ = freshness(entries, dep, seen)
        if d_status != "valid":
            return "stale", f"의존 항목 {dep}: {d_status}"
        if entries[dep].get("version") != version:
            return "stale", f"의존 항목 {dep} 갱신됨"
    return "valid", ""


def sections(text: str) -> dict:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, name = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1)
            out[name] = []
        elif name:
            out[name].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def body_problems(kind: str, folder: Path) -> list:
    problems = []
    for name, required in KINDS[kind]["required"].items():
        p = folder / name
        if not p.exists():
            problems.append(f"{name}: 파일 없음")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if not required:
            if not re.sub(r"<!--.*?-->", "", text, flags=re.S).strip():
                problems.append(f"{name}: 비어 있음")
            continue
        found = sections(text)
        for sec in required:
            if not found.get(sec):
                problems.append(f"{name}: '## {sec}' 섹션이 비어 있음")
    return problems


def first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("-*#>0123456789. ").strip()
        if line and not line.startswith("|---"):
            return line.strip("| ")[:120]
    return ""


def score(e: dict, query: str) -> int:
    q = query.lower()
    hay = " ".join([e["id"].replace("/", " "), e.get("q", ""), e.get("summary", ""),
                    " ".join(e.get("tags", [])), " ".join(e.get("serves", []))]).lower()
    # Korean particles stick to words ("이상치를"), so match substrings in both directions.
    s = max(sum(1 for t in set(TOKEN.findall(q)) if t in hay),
            sum(1 for t in set(TOKEN.findall(hay)) if t in q))
    s += 2 * sum(1 for r in e.get("serves", []) if r.lower() in q)
    return s + (5 if e["id"].lower() in q else 0)


def write_index(entries=None) -> None:
    entries = load() if entries is None else entries
    states = {eid: freshness(entries, eid) for eid in entries}
    counts = {s: sum(1 for st, _ in states.values() if st == s) for s in STATUSES}
    lines = ["# ctx INDEX", "",
             "> 자동 생성 파일 — 직접 고치지 말 것 (`python3 .harness/bin/ctx.py index`).",
             "> 작업 전 `ctx.py find <키워드>` → `valid`는 재사용, `stale`은 그대로 쓰지 말 것.", "",
             "항목 {} · ".format(len(entries)) + " · ".join(f"{s} {n}" for s, n in counts.items()), ""]
    for kind, spec in KINDS.items():
        rows = sorted((e for e in entries.values() if e.get("kind") == kind), key=lambda e: e["id"])
        if not rows:
            continue
        lines += [f"## {kind}", "", "| ID | 상태 | 한 줄 | 관련 R | 갱신 |", "|---|---|---|---|---|"]
        for e in rows:
            st, why = states[e["id"]]
            label = f"{st} ({why})" if st == "stale" and why else st
            text = (e.get("summary") or e.get("q", "")).replace("|", "\\|")[:100]
            lines.append(f"| [{e['id']}]({e['id']}/{spec['main']}) | {label} | {text} | "
                         f"{','.join(e.get('serves', []))} | {e.get('updated', '')[5:16]} |")
        lines.append("")
    CTX.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_MD.with_name(f".INDEX.{os.getpid()}.tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(tmp, INDEX_MD)


def split_csv(v) -> list:
    return [x.strip() for x in (v or "").split(",") if x.strip()]


# ---------------------------------------------------------------- commands

def cmd_init(a) -> int:
    CTX.mkdir(parents=True, exist_ok=True)
    EVENTS.touch()
    write_index()
    print(f"[ctx] {rel(str(CTX))}/ 준비됨 — INDEX.md, index.jsonl")
    return 0


def cmd_new(a) -> int:
    if a.kind not in KINDS:
        print(f"[ctx] 종류는 {', '.join(KINDS)} 중 하나")
        return 2
    if not SLUG.match(a.slug):
        print("[ctx] SLUG는 영문 소문자·숫자·-._ (48자 이하). 예: anomaly-method")
        return 2
    eid = f"{a.kind}/{a.slug}"
    entries = load()
    if eid in entries:
        status, why = freshness(entries, eid)
        if status == "draft" and not a.redo:
            print(f"[ctx] {eid} 는 이미 작성 중 → ctx/{eid}/ 에 이어서 쓰고 `ctx.py done {eid}`")
            return 0
        if not a.redo:
            print(f"[ctx] 이미 기록 있음: {eid} [{status}{' — ' + why if why else ''}]")
            print(f"      재조사하지 말고 `ctx.py get {eid}` 로 읽어서 재사용. 다시 하려면 --redo.")
            return 3
    elif not a.q:
        print("[ctx] 새 항목은 --q (무엇을 묻는지/목적) 가 필요")
        return 2
    for dep in a.uses:
        if dep not in entries:
            print(f"[ctx] 경고: 의존 항목 {dep} 기록 없음")
    folder = CTX / a.kind / a.slug
    folder.mkdir(parents=True, exist_ok=True)
    q = a.q or entries.get(eid, {}).get("q", "")
    serves = split_csv(a.serves) or entries.get(eid, {}).get("serves", [])
    for name, tpl in KINDS[a.kind]["files"].items():
        if a.redo and (folder / name).exists():  # start from a blank body; keep the old one for comparison
            (folder / "_prev").mkdir(exist_ok=True)
            os.replace(folder / name, folder / "_prev" / name)
        if not (folder / name).exists():
            text = tpl.replace("{id}", eid).replace("{q}", q).replace("{serves}", ", ".join(serves) or "-")
            (folder / name).write_text(text, encoding="utf-8")
    event = {"op": "new", "id": eid, "kind": a.kind, "status": "draft"}
    if a.q:
        event["q"] = a.q
    if a.serves:
        event["serves"] = serves
    if a.inputs:
        event["inputs"] = [rel(x) for x in a.inputs]
    if a.uses:
        event["uses"] = a.uses
    if a.tags:
        event["tags"] = split_csv(a.tags)
    append(event)
    write_index()
    files = ", ".join(n for n in KINDS[a.kind]["files"])
    print(f"[ctx] {eid} 작성 시작 → ctx/{eid}/ ({files})")
    print(f"      본문을 채운 뒤 `python3 .harness/bin/ctx.py done {eid}`")
    return 0


def cmd_done(a) -> int:
    entries = load()
    e = entries.get(a.id)
    if e is None:
        print(f"[ctx] 기록 없음: {a.id} (먼저 `ctx.py new`)")
        return 2
    kind = e["kind"]
    folder = CTX / a.id
    problems = body_problems(kind, folder)
    inputs = list(dict.fromkeys(e.get("inputs", []) + [rel(x) for x in a.inputs]))
    problems += [f"입력 파일 없음: {p}" for p in inputs if not (ROOT / p).exists()]
    for dep in e.get("uses", []):
        status, _ = freshness(entries, dep)
        if status != "valid":
            problems.append(f"의존 항목 {dep} 이(가) {status} — 먼저 정리할 것")
    summary = a.summary
    if not summary:
        main = folder / KINDS[kind]["main"]
        if main.exists():
            summary = first_line(sections(main.read_text(encoding="utf-8", errors="replace"))
                                 .get(KINDS[kind]["summary"], ""))
    if not summary:
        problems.append("한 줄 요약 없음 (--summary 또는 요약 섹션 첫 줄)")
    if problems:
        print(f"[ctx] {a.id} 완료 거부:")
        for p in problems:
            print(f"  - {p}")
        return 1
    append({"op": "done", "id": a.id, "status": "valid", "summary": summary, "inputs": inputs,
            "snap": {p: signature(p) for p in inputs},
            "dep_ver": {d: entries[d].get("version") for d in e.get("uses", [])},
            "version": f"{time.time():.6f}", "note": ""})
    write_index()
    print(f"[ctx] {a.id} valid — {summary}")
    return 0


def cmd_find(a) -> int:
    entries = load()
    query = " ".join(a.words)
    ranked = [(score(e, query) if query else 1, e) for e in entries.values()]
    ranked = sorted((r for r in ranked if r[0] > 0), key=lambda r: (-r[0], r[1]["id"]))[: a.limit]
    if not ranked:
        print(f"[ctx] '{query}' 관련 기록 없음 → 새로 작업: `ctx.py new <kind> <slug> --q ...`")
        return 0
    for _, e in ranked:
        status, why = freshness(entries, e["id"])
        tail = f"  ({why})" if why else ""
        print(f"{status:<10} {e['id']:<32} {(e.get('summary') or e.get('q', ''))[:90]}{tail}")
    print("→ valid: `ctx.py get <ID>` 로 읽고 재사용(재조사 금지) · stale: 다시 하거나 확인 후 사용 · draft: 이어서 작성")
    return 0


def cmd_get(a) -> int:
    entries = load()
    e = entries.get(a.id)
    if e is None:
        print(f"[ctx] 기록 없음: {a.id}")
        return cmd_find(argparse.Namespace(words=[a.id.replace("/", " ")], limit=5)) or 1
    status, why = freshness(entries, a.id)
    print(f"# {a.id}  [{status}{' — ' + why if why else ''}]")
    for label, key in (("질문/목적", "q"), ("요약", "summary"), ("관련 R", "serves"), ("입력", "inputs"),
                       ("의존", "uses"), ("태그", "tags"), ("대체", "by"), ("갱신", "updated")):
        v = e.get(key)
        if v:
            print(f"- {label}: {', '.join(v) if isinstance(v, list) else v}")
    if status == "stale":
        print(f"⚠ 오래된 기록: 근거로 그대로 쓰지 말 것. 다시 하려면 `ctx.py new {e['kind']} {a.id.split('/', 1)[1]} --redo`")
    folder = CTX / a.id
    names = sorted(p.name for p in folder.iterdir() if p.is_file()) if a.all and folder.is_dir() \
        else [KINDS[e["kind"]]["main"]]
    for name in names:
        p = folder / name
        print(f"\n---- ctx/{a.id}/{name} ----")
        print(p.read_text(encoding="utf-8", errors="replace").rstrip() if p.exists() else "(파일 없음)")
    return 0


def cmd_status(a) -> int:
    entries = load()
    if a.id not in entries:
        print(f"[ctx] 기록 없음: {a.id}")
        return 2
    if a.by and a.by not in entries:
        print(f"[ctx] 대체 항목 기록 없음: {a.by}")
        return 2
    if a.status == "valid" and entries[a.id].get("status") != "valid":
        print("[ctx] valid 로 바꾸려면 `ctx.py done` (본문 검증) 을 쓸 것")
        return 2
    event = {"op": "status", "id": a.id, "status": a.status, "note": a.note or ""}
    if a.by:
        event["by"] = a.by
    append(event)
    write_index()
    print(f"[ctx] {a.id} → {a.status}")
    return 0


def cmd_state(a) -> int:
    print(freshness(load(), a.id)[0])
    return 0


def cmd_check(a) -> int:
    entries = load()
    states = {eid: freshness(entries, eid) for eid in entries}
    problems = 0
    for eid, (status, why) in sorted(states.items()):
        if status == "valid":
            bad = body_problems(entries[eid]["kind"], CTX / eid)
            if bad:
                problems += 1
                print(f"  ! {eid}: valid 인데 본문 문제 — {'; '.join(bad)}")
        elif status == "stale":
            print(f"  ~ {eid}: stale — {why}")
    write_index(entries)
    counts = {s: sum(1 for st, _ in states.values() if st == s) for s in STATUSES}
    print(f"[ctx] 항목 {len(entries)} · " + " · ".join(f"{s} {n}" for s, n in counts.items()) +
          (f" · 본문 문제 {problems}" if problems else ""))
    return 1 if problems else 0


def cmd_index(a) -> int:
    write_index()
    print(f"[ctx] {rel(str(INDEX_MD))} 갱신")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(prog="ctx.py", description="ctx/ 작업 기억 저장소")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    p = sub.add_parser("new")
    p.add_argument("kind")
    p.add_argument("slug")
    p.add_argument("--q", help="무엇을 묻는지/목적 (검색 대상)")
    p.add_argument("--serves", help="관련 요구사항 ID, 쉼표 구분 (R-1,R-2)")
    p.add_argument("--inputs", nargs="*", default=[], help="바뀌면 이 기록을 stale로 만드는 파일")
    p.add_argument("--uses", nargs="*", default=[], help="이 기록이 근거로 쓰는 ctx ID")
    p.add_argument("--tags")
    p.add_argument("--redo", action="store_true", help="기존 기록을 다시 작성")
    p.set_defaults(fn=cmd_new)
    p = sub.add_parser("done")
    p.add_argument("id")
    p.add_argument("--summary")
    p.add_argument("--inputs", nargs="*", default=[])
    p.set_defaults(fn=cmd_done)
    p = sub.add_parser("find")
    p.add_argument("words", nargs="*")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("get")
    p.add_argument("id")
    p.add_argument("--all", action="store_true", help="폴더의 모든 파일 출력")
    p.set_defaults(fn=cmd_get)
    p = sub.add_parser("status")
    p.add_argument("id")
    p.add_argument("status", choices=STATUSES)
    p.add_argument("--by")
    p.add_argument("--note")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("state")
    p.add_argument("id")
    p.set_defaults(fn=cmd_state)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
