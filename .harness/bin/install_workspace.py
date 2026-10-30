#!/usr/bin/env python3
"""Copy the harness into a designated task workspace without overwriting its files."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--no-commit", action="store_true", help="Compatibility: commits are always manual")
    args = parser.parse_args()
    target = args.workspace.resolve()
    if target == SOURCE:
        return subprocess.call([sys.executable, str(SOURCE / ".harness/bin/environment.py"), "setup"])
    if not target.is_dir():
        parser.error("작업 폴더가 없습니다. 주최 측이 지정한 폴더를 확인하세요.")
    if not shutil.which("git"):
        parser.error("Git을 찾지 못했습니다. docs/SETUP.md의 도구 복구 안내를 확인하세요.")
    conflicts = []
    paths = [SOURCE / "AGENTS.md", SOURCE / "setup.sh"]
    for directory in (".agents/skills", ".codex", ".harness/bin", ".harness/tests", "prompts"):
        paths.extend(p for p in (SOURCE / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for name in ("INTENT", "VERIFICATION", "WORKLOG", "SETUP"):
        paths.append(SOURCE / f"docs/{name}.md")
    for source in paths:
        dest = target / source.relative_to(SOURCE)
        if dest.exists():
            if dest.read_bytes() != source.read_bytes():
                conflicts.append(str(source.relative_to(SOURCE)))
                if source.name == "AGENTS.md":
                    alternative = target / "AGENTS.harness.md"
                    if not alternative.exists():
                        shutil.copy2(source, alternative)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    git = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], capture_output=True)
    if git.returncode:
        subprocess.run(["git", "-C", str(target), "init", "-q"], check=True)
    result = subprocess.call([sys.executable, str(target / ".harness/bin/environment.py"), "setup"])
    print("과제 README 및 기존 파일을 보존했습니다. 설치 변경은 검토 후 직접 커밋하세요.")
    if conflicts:
        print("확인 필요: 기존 파일과 다른 하네스 파일을 덮어쓰지 않았습니다:\n  " + "\n  ".join(conflicts))
        print("AGENTS.md 충돌 시 AGENTS.harness.md를 검토해 필요한 지침을 합치세요.")
    return int(bool(result or conflicts))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
