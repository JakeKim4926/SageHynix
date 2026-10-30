#!/usr/bin/env python3
"""표 데이터 프로파일 — 사실만 출력한다(해석은 docs/research/data-profile.md ## 결론에).

Usage:
    python3 .agents/skills/analyze/scripts/profile_data.py <파일>...   # .csv .tsv .jsonl

Standard library only: 패키지 설치 없이 과제 시작 직후 바로 돌린다.
다른 형식(Excel·Parquet 등)은 읽지 않고 그렇다고 출력한다(SKILL ① 2단계).
Self-test: python3 -m unittest discover -s .agents/skills/analyze/scripts -p "test_*.py"
"""
import csv
import io
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

MISSING = {"", "na", "n/a", "nan", "null", "none"}
DATE_FORMATS = ("%Y/%m/%d", "%Y/%m/%d %H:%M:%S", "%Y.%m.%d", "%Y.%m.%d %H:%M:%S")
DIST_MAX_UNIQUE = 10  # 고유값이 이 이하이고 반복이 있으면 값 분포를 보인다
DIST_TOP = 5


# ---------------------------------------------------------------- reading

def read_text(path: Path):
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp949"), "cp949"  # 국내 엑셀 저장 CSV


def read_table(path: Path):
    """Return (header, rows, encoding, ragged) or None for unsupported formats."""
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        text, enc = read_text(path)
        reader = csv.reader(io.StringIO(text, newline=""), delimiter="\t" if ext == ".tsv" else ",")
        records = [r for r in reader if r]
        if not records:
            return [], [], enc, 0
        header, body = records[0], records[1:]
        ragged = sum(1 for r in body if len(r) != len(header))
        rows = [[r[i] if i < len(r) else "" for i in range(len(header))] for r in body]
        return header, rows, enc, ragged
    if ext == ".jsonl":
        text, enc = read_text(path)
        objs = [json.loads(line) for line in text.splitlines() if line.strip()]
        header = list(dict.fromkeys(k for o in objs for k in o))
        rows = [["" if o.get(k) is None else str(o[k]) for k in header] for o in objs]
        return header, rows, enc, 0
    return None


# ---------------------------------------------------------------- typing

def as_date(s: str):
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def column_type(values):
    """(타입 이름, 정렬 키 함수). values는 결측을 뺀 문자열."""
    def all_parse(fn):
        try:
            return all(fn(v) is not None for v in values)
        except ValueError:
            return False
    if all_parse(int):
        return "정수", int
    if all_parse(float):
        return "실수", float
    if all_parse(as_date):
        return "날짜", as_date
    return "문자열", None


def describe(values, n_rows: int):
    present = [v.strip() for v in values if v.strip().lower() not in MISSING]
    missing = n_rows - len(present)
    counts = Counter(present)
    kind, key = column_type(present) if present else ("결측만", None)
    notes = []
    if kind in ("정수", "문자열") and not missing and len(counts) == n_rows:
        notes.append("키 후보")  # 실수·날짜는 값이 모두 달라도 측정값일 가능성이 커서 제외
    if key:
        notes.append(f"{min(present, key=key)} ~ {max(present, key=key)}")
    if len(counts) <= DIST_MAX_UNIQUE and len(counts) < len(present):
        top = ", ".join(f"{v} {c}" for v, c in counts.most_common(DIST_TOP))
        notes.append(f"값 분포: {top}{' …' if len(counts) > DIST_TOP else ''}")
    rate = f"{missing / n_rows * 100:.1f}%" if n_rows else "-"
    return kind, rate, len(counts), " · ".join(notes)


# ---------------------------------------------------------------- report

def profile(path) -> str:
    path = Path(path)
    table = read_table(path)
    if table is None:
        return (f"### {path.name}\n- 이 스크립트는 '{path.suffix or '확장자 없음'}' 형식을 읽지 않음 — "
                "pandas로 열거나 직접 열어 같은 항목을 기록 (analyze SKILL ① 2단계)")
    header, rows, enc, ragged = table
    if not header:
        return f"### {path.name} (인코딩 {enc})\n- 빈 파일"
    dup = len(rows) - len({tuple(r) for r in rows})
    lines = [f"### {path.name} (인코딩 {enc})",
             f"- 행 {len(rows)} · 열 {len(header)} · 중복 행 {dup}"
             + (f" · 열 수가 헤더와 다른 행 {ragged}" if ragged else ""),
             "- 결측 기준: 빈 칸, NA, N/A, NaN, null, None (대소문자 무시)",
             "",
             "| 열 | 타입 | 결측률 | 고유값 | 범위·분포 |",
             "|---|---|---|---|---|"]
    for i, name in enumerate(header):
        kind, rate, n_unique, notes = describe([r[i] for r in rows], len(rows))
        lines.append(f"| {name} | {kind} | {rate} | {n_unique} | {notes} |")
    return "\n".join(lines)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    print("\n\n".join(profile(p) for p in sys.argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
