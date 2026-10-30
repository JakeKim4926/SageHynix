#!/usr/bin/env python3
"""Environment diagnosis and opt-in dependency installation. Standard library only."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILES = {
    "verify": {"pytest": "pytest", "ruff": "ruff"},
    "data": {"pandas": "pandas", "numpy": "numpy"},
    "excel": {"pandas": "pandas", "openpyxl": "openpyxl", "xlrd": "xlrd"},
    "parquet": {"pandas": "pandas", "pyarrow": "pyarrow"},
    "api": {"fastapi": "fastapi", "uvicorn": "uvicorn"},
    "dashboard": {"streamlit": "streamlit"},
    "plot": {"matplotlib": "matplotlib"},
    "ml": {"sklearn": "scikit-learn"},
}
SKILLS = "research verify doc fe-setup fe-build fe-design".split()
AGENTS = "researcher verifier".split()


def run(args, **kwargs):
    try:
        args = [shutil.which(str(args[0])) or str(args[0]), *args[1:]]
        return subprocess.run(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                              capture_output=True, timeout=30, **kwargs)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(args, 1, "", str(exc))


def packages(profiles):
    return {module: package for profile in profiles for module, package in PROFILES[profile].items()}


def import_ok(python, module):
    return run([str(python), "-c", "import importlib,sys; importlib.import_module(sys.argv[1])", module]).returncode == 0


def check(profiles):
    failures = []

    def report(ok, label):
        print(f"{'OK' if ok else 'FAIL'}  {label}")
        if not ok:
            failures.append(label)

    print(f"[환경] {sys.platform} / Python {sys.version.split()[0]} / {sys.executable}")
    report(sys.version_info >= (3, 9), "Python 3.9+")
    for tool in ("bash", "git", "codex"):
        result = run([tool, "--version"])
        version = (result.stdout or result.stderr).splitlines()
        report(result.returncode == 0, f"{tool}: {version[0] if version else '실행 불가'}")
    report(run(["bash", "-c", "(( BASH_VERSINFO[0] >= 4 ))"]).returncode == 0, "Bash 4+")
    repo = run(["git", "rev-parse", "--show-toplevel"])
    report(repo.returncode == 0 and Path(repo.stdout.strip()).resolve() == ROOT, "현재 폴더가 Git 작업 공간 루트")
    for relative in ("AGENTS.md", ".codex/config.toml", ".codex/hooks/harness_hook.py",
                     ".codex/rules/harness.rules", "prompts/SCRIPT.md"):
        report((ROOT / relative).is_file(), relative)
    for skill in SKILLS:
        path = ROOT / ".agents/skills" / skill / "SKILL.md"
        report(path.is_file() and f"name: {skill}\n" in path.read_text(encoding="utf-8"), f"skill: {skill}")
    report(all((ROOT / f".codex/agents/{agent}.toml").is_file() for agent in AGENTS), f"서브에이전트 정의 {len(AGENTS)}개")
    try:
        hooks = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        report(all(event in hooks["hooks"] for event in ("SessionStart", "UserPromptSubmit", "PreToolUse")), "훅 JSON 및 이벤트 3개")
    except (OSError, ValueError, KeyError, TypeError):
        report(False, "훅 JSON 및 이벤트 3개")
    for command, deny in (("git push origin main", True), ("echo x >> .codex/hooks.json", True),
                          ("python3 -m pytest -q", False)):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)})
        result = run([sys.executable, str(ROOT / ".codex/hooks/harness_hook.py"), "pretool"],
                     input=payload, env={**os.environ, "HYNIX_HARNESS_NOLOG": "1"})
        report(result.returncode == 0 and (('"deny"' in result.stdout) if deny else not result.stdout.strip()), f"guard: {command}")
    for module, package in packages(profiles).items():
        report(import_ok(sys.executable, module), f"선택 의존성: {package}")
    if any((ROOT / path).is_file() for path in ("package.json", "frontend/package.json")):
        for tool in ("node", "npm"):
            report(run([tool, "--version"]).returncode == 0, f"package.json 실행 도구: {tool}")
    print("선택 기능: " + ", ".join(PROFILES) + " (필요한 것만 --profile로 검사)")
    print("[수동 확인 필요] 과제/제출 폴더, Codex 프로젝트·훅 신뢰, 모델, 실제 skill/서브에이전트 노출.")
    print("문제 복구 및 수동 확인 방법: docs/SETUP.md")
    print(f"{'시작 불가' if failures else '자동 점검 통과 (수동 확인은 별도)'}: 실패 {len(failures)}개")
    return int(bool(failures))


def append_lines(path, lines):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in lines if line not in old.splitlines()]
    if missing:
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(("\n" if old and not old.endswith("\n") else "") + "\n".join(missing) + "\n")


def initialize():
    result = run(["git", "rev-parse", "--show-toplevel"])
    if result.returncode or Path(result.stdout.strip()).resolve() != ROOT:
        print("FAIL: 먼저 이 폴더를 Git 저장소 루트로 준비하세요. docs/SETUP.md 참고.")
        return False
    append_lines(ROOT / ".gitignore", [".venv/", "__pycache__/", "*.pyc", ".harness/log/", ".harness/state/"])
    for path in (ROOT / ".harness/bin").glob("*.sh"):
        path.chmod(path.stat().st_mode | 0o111)
    for path in (ROOT / ".agents/skills").glob("*/scripts/*.py"):
        path.chmod(path.stat().st_mode | 0o111)
    (ROOT / "docs/research").mkdir(parents=True, exist_ok=True)
    print("준비 완료: 실행 권한, Git 제외 설정, docs/research/")
    return True


def install(profiles):
    wanted = packages(profiles)
    if all(import_ok(sys.executable, module) for module in wanted):
        print("선택한 패키지가 모두 사용 가능합니다. 설치 생략.")
        return Path(sys.executable)
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")
    if not python.exists():
        # Reuse platform packages; install missing packages only inside this project.
        result = run([sys.executable, "-m", "venv", "--system-site-packages", str(ROOT / ".venv")])
        if result.returncode:
            print("FAIL: 가상환경 생성 실패. python3-venv/권한을 확인하세요. docs/SETUP.md 참고.")
            print(result.stderr)
            return None
    if run([str(python), "-m", "pip", "--version"]).returncode:
        print("FAIL: 가상환경 pip 실행 불가. docs/SETUP.md 참고.")
        return None
    missing = [package for module, package in wanted.items() if not import_ok(python, module)]
    if missing:
        print("프로젝트 환경에 설치: " + ", ".join(missing), flush=True)
        rc = subprocess.call([str(python), "-m", "pip", "--disable-pip-version-check", "install", *missing], cwd=ROOT)
        if rc:
            print("FAIL: 설치 실패. 네트워크/패키지 인덱스/권한을 확인하고 같은 명령으로 재시도하세요.")
            return None
    if not all(import_ok(python, module) for module in wanted):
        print("FAIL: 설치 후 import 실패. 환경 충돌을 확인하세요. docs/SETUP.md 참고.")
        return None
    append_lines(ROOT / ".harness/requirements.local.txt", list(wanted.values()))
    return python


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "setup"))
    parser.add_argument("--profile", nargs="+", choices=PROFILES, default=[])
    parser.add_argument("--install", nargs="+", choices=PROFILES, default=[])
    args = parser.parse_args()
    if args.action == "check" and args.install:
        parser.error("설치는 bash setup.sh --install <기능>으로 실행하세요")
    if args.action == "setup":
        if not initialize():
            return 1
        if args.install:
            python = install(args.install)
            if python is None:
                return 1
            return subprocess.call([str(python), str(Path(__file__).resolve()), "check", "--profile", *dict.fromkeys(args.profile + args.install)], cwd=ROOT)
    return check(args.profile)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
