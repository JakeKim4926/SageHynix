#!/usr/bin/env python3
"""Quick, honest data profile in Markdown.

    profile_data.py FILE [FILE ...] [--max-rows N]

Uses pandas when available; falls back to the csv module (CSV/TSV only).
Every number printed is computed here — nothing is estimated.
"""
import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover - depends on environment
    pd = None


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def fmt(v, digits=4):
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        return f"{v:.{digits}g}"
    return str(v)


# ---------------------------------------------------------------- pandas path

def load_pandas(path: Path, max_rows):
    suf = path.suffix.lower()
    if suf in (".csv", ".txt"):
        return pd.read_csv(path, nrows=max_rows, low_memory=False)
    if suf == ".tsv":
        return pd.read_csv(path, sep="\t", nrows=max_rows, low_memory=False)
    if suf in (".xlsx", ".xls"):
        return pd.read_excel(path, nrows=max_rows)
    if suf == ".parquet":
        df = pd.read_parquet(path)
        return df.head(max_rows) if max_rows else df
    if suf in (".json", ".jsonl"):
        df = pd.read_json(path, lines=suf == ".jsonl")
        return df.head(max_rows) if max_rows else df
    raise ValueError(f"지원하지 않는 형식: {suf}")


def profile_pandas(path: Path, max_rows):
    df = load_pandas(path, max_rows)
    n = len(df)
    lines = [f"- 행 {n:,} · 열 {df.shape[1]}" + (f" (앞 {max_rows:,}행 표본)" if max_rows and n >= max_rows else "")]
    dup = int(df.duplicated().sum())
    lines.append(f"- 완전 중복 행: {dup:,} ({dup / n:.2%})" if n else "- 빈 파일")
    rows = []
    for col in df.columns:
        s = df[col]
        nn = int(s.isna().sum())
        nun = int(s.nunique(dropna=True))
        ex = ", ".join(map(str, s.dropna().unique()[:3]))[:60]
        rows.append([col, str(s.dtype), f"{nn / n:.1%}" if n else "-", nun,
                     "예" if n and nun == n - nn and nn == 0 else "", ex])
    lines.append("\n" + md_table(["컬럼", "dtype", "결측률", "고유값", "키 후보", "예시"], rows))

    num = df.select_dtypes("number")
    if not num.empty:
        desc = num.describe().T
        nrows = []
        for col, r in desc.iterrows():
            q1, q3 = r["25%"], r["75%"]
            iqr = q3 - q1
            outl = int(((num[col] < q1 - 1.5 * iqr) | (num[col] > q3 + 1.5 * iqr)).sum()) if iqr == iqr else 0
            nrows.append([col, fmt(r["mean"]), fmt(r["std"]), fmt(r["min"]), fmt(r["50%"]), fmt(r["max"]), outl])
        lines.append("\n**수치형 요약** (이상치 = 1.5×IQR 밖 개수)\n\n" +
                     md_table(["컬럼", "평균", "표준편차", "최소", "중앙값", "최대", "이상치"], nrows))

    # pandas >= 3 reports text columns as "str", older versions as object.
    text_cols = [c for c in df.columns
                 if df[c].dtype == object or pd.api.types.is_string_dtype(df[c].dtype)]
    cat = [c for c in text_cols if 1 < df[c].nunique() <= 30]
    for col in cat[:8]:
        vc = df[col].value_counts(dropna=False).head(10)
        lines.append(f"\n**{col}** 상위 값: " + ", ".join(f"{k}({v})" for k, v in vc.items()))

    for col in text_cols:
        if any(k in str(col).lower() for k in ("date", "time", "dt", "일자", "시각")):
            parsed = pd.to_datetime(df[col], errors="coerce")
            ok = parsed.notna().mean() if n else 0
            if ok > 0.8:
                lines.append(f"\n**{col}** 날짜 해석 {ok:.0%}: {parsed.min()} ~ {parsed.max()}")
    return "\n".join(lines)


# ---------------------------------------------------------------- stdlib fallback

def profile_stdlib(path: Path, max_rows):
    if path.suffix.lower() not in (".csv", ".tsv", ".txt"):
        return f"- pandas 미설치로 {path.suffix} 형식은 프로파일 불가 (`pip install pandas openpyxl pyarrow`)"
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, [])
        cols = [[] for _ in header]
        n = 0
        seen = Counter()
        for row in reader:
            if max_rows and n >= max_rows:
                break
            n += 1
            seen[tuple(row)] += 1
            for i, _ in enumerate(header):
                cols[i].append(row[i] if i < len(row) else "")
    dup = sum(c - 1 for c in seen.values() if c > 1)
    lines = [f"- 행 {n:,} · 열 {len(header)} (pandas 없음: 표준 라이브러리 프로파일)",
             f"- 완전 중복 행: {dup:,}"]
    rows = []
    for name, vals in zip(header, cols):
        missing = sum(1 for v in vals if v.strip() in ("", "NA", "NaN", "null", "None"))
        nums = []
        for v in vals:
            try:
                nums.append(float(v))
            except ValueError:
                pass
        kind = "numeric" if vals and len(nums) >= 0.9 * (len(vals) - missing) and nums else "text"
        stat = f"{min(nums):.4g}~{max(nums):.4g}, 평균 {sum(nums) / len(nums):.4g}" if kind == "numeric" else ""
        rows.append([name, kind, f"{missing / n:.1%}" if n else "-", len(set(vals)), stat,
                     ", ".join(list(dict.fromkeys(v for v in vals if v))[:3])[:60]])
    lines.append("\n" + md_table(["컬럼", "유형", "결측률", "고유값", "범위/평균", "예시"], rows))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max-rows", type=int, default=0, help="0 = 전체")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print("# 데이터 프로파일\n")
    print(f"- 엔진: {'pandas ' + pd.__version__ if pd else '표준 라이브러리 csv'}")
    print(f"- 명령: `profile_data.py {' '.join(sys.argv[1:])}`\n")
    for f in a.files:
        p = Path(f)
        print(f"\n## {p} ({p.stat().st_size:,} bytes)\n" if p.exists() else f"\n## {p}\n")
        if not p.exists():
            print("- 파일 없음")
            continue
        try:
            print(profile_pandas(p, a.max_rows or None) if pd else profile_stdlib(p, a.max_rows))
        except Exception as e:  # report, don't hide
            print(f"- 프로파일 실패: `{e!r}`")
    print("\n## 사람이 채울 것\n- 컬럼 의미 추정 / 키·조인 / 함정 / 분석 영향 (SKILL.md 참고)")


if __name__ == "__main__":
    main()
