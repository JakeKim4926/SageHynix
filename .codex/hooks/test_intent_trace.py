"""Self-tests for the intent trace gate. Real `git commit` in a temp repo, through .codex/hooks/git.

Run: python3 -m unittest discover -s .codex/hooks -p "test_*.py"   (pytest도 가능)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))
os.environ["HYNIX_HARNESS_NOLOG"] = "1"
import harness_hook  # noqa: E402

INTENT_V1 = """# INTENT
| AC | R | P | 우선 | 원문 근거 | 수용 기준 | 상태 |
|---|---|---|---|---|---|---|
| AC-1.1 | R-1 | P-1 | M | docs/task/README.md:3 | 이상 설비 recall ≥ 0.9 | 승인 |
"""
INTENT_V2 = INTENT_V1.replace("recall ≥ 0.9", "accuracy ≥ 0.95")
INTENT_TWO = INTENT_V1 + "| AC-1.2 | R-1 | P-1 | S | A-1 | 추론 1초 이내 | 승인 |\n"


def line(**event) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def verify(result, ac="AC-1.1") -> str:
    return line(type="verify", refs=[ac], result=result,
                line=f"{result} 탐지(R-1) — 검증셋 → recall 0.93 (python3 -m pytest -q tests/test_detect.py)")


class GitHooks(unittest.TestCase):
    def setUp(self):
        self.make_repo()
        self.write("docs/task/README.md", "# 과제\n\n이상 징후를 놓치지 않도록 탐지한다.\n")
        self.commit("chore: 과제 원본 반입")  # 저장소 첫 커밋만 main에 직접
        self.git("switch", "-q", "-c", "work")

    def make_repo(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        (self.repo / ".codex/hooks/git").mkdir(parents=True)
        shutil.copy(HOOKS / "intent_trace.py", self.repo / ".codex/hooks")
        for src in (HOOKS / "git").iterdir():
            dst = self.repo / ".codex/hooks/git" / src.name
            shutil.copy(src, dst)
            os.chmod(dst, 0o755)
        for args in (["init", "-q", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"],
                     ["config", "core.hooksPath", ".codex/hooks/git"]):
            self.git(*args)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, encoding="utf-8")

    def write(self, rel, text, mode="w"):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode, encoding="utf-8", newline="\n") as f:
            f.write(text)

    def commit(self, msg, ok=True, expect=None):
        self.git("add", "-A")
        r = self.git("commit", "-q", "-m", msg)
        self.assertEqual(r.returncode == 0, ok, r.stderr)
        if expect:
            self.assertIn(expect, r.stderr)
        if not ok:
            self.git("reset", "-q")  # unstage only; keep worktree for the next step
        return r

    def contract(self):
        self.write("docs/INTENT.md", INTENT_V1)
        self.write("docs/ledger.jsonl", line(type="decision", id="D-1", refs=["AC-1.1"], what="AC 승인",
                                             why="원문 3줄", by="user"))
        self.commit("docs(intent): 의도 계약 — P-1")

    def test_task_original_is_add_only(self):
        self.write("docs/task/data.md", "추가 자료\n")
        self.commit("chore: 자료 반입")
        self.write("docs/task/README.md", "# 과제\n\n정확도를 높인다.\n")
        self.commit("chore: x", ok=False, expect="[harness guard] docs/task/README.md")

    def test_ac_change_needs_decision_in_same_commit(self):
        self.contract()
        self.write("docs/INTENT.md", INTENT_V2)
        self.commit("docs(intent): 지표 변경", ok=False, expect="[harness guard] AC-1.1")
        self.write("docs/ledger.jsonl", line(type="decision", id="D-2", refs=["R-1"], what="recall→accuracy",
                                             why="담당자 답변", by="user"), mode="a")
        self.commit("docs(intent): 지표 변경 — D-2")

    def test_ac_row_needs_source(self):
        self.write("docs/INTENT.md", INTENT_V1.replace("docs/task/README.md:3", "원문"))
        self.commit("docs(intent): 계약", ok=False, expect="[trace check] docs/INTENT.md: AC-1.1")

    def test_ledger_is_append_only_and_valid(self):
        self.contract()
        self.write("docs/ledger.jsonl", line(type="decision", id="D-1", refs=["AC-1.1"], what="AC 승인",
                                             why="원문 3줄", by="agent"))
        self.commit("docs: x", ok=False, expect="docs/ledger.jsonl:1 기존 줄")
        self.git("checkout", "--", "docs/ledger.jsonl")
        self.write("docs/ledger.jsonl", '{"type":"verify", refs:[]}\n', mode="a")
        self.commit("docs: x", ok=False, expect="docs/ledger.jsonl:2 JSON 오류")

    def test_feat_needs_r_id_and_latest_pass(self):
        self.contract()
        self.write("src.py", "x = 1\n")
        self.commit("feat(detect): 이상 탐지", ok=False, expect="R-n 필요")
        self.commit("feat(detect): 이상 탐지 — R-1", ok=False, expect="R-1: 스테이징된 docs/ledger.jsonl에 이번 커밋에서 추가한 verify PASS 없음")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1")
        self.write("src.py", "x = 2\n")
        self.write("docs/ledger.jsonl", verify("FAIL"), mode="a")
        self.commit("fix(detect): 임계값 — R-1", ok=False, expect="최신 FAIL: AC-1.1")
        self.commit("test(detect): 경계값 추가")  # feat·fix만 검사

    def test_fix_needs_pass_added_in_this_commit(self):
        """이전 커밋의 PASS로는 새 feat·fix를 통과시키지 않는다."""
        self.contract()
        self.write("src.py", "x = 1\n")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1")
        self.write("src.py", "x = 2\n")
        self.commit("fix(detect): 임계값 — R-1", ok=False, expect="R-1: 스테이징된 docs/ledger.jsonl에 이번 커밋에서 추가한 verify PASS 없음")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("fix(detect): 임계값 — R-1")

    def test_feat_needs_intent_once_task_exists(self):
        """원문을 반입했으면 $intent를 건너뛴 feat·fix는 막는다."""
        self.write("src.py", "x = 1\n")
        self.commit("feat(detect): 이상 탐지 — R-1", ok=False, expect="docs/INTENT.md가 없음")

    def test_no_task_means_no_checks(self):
        """과제 원문도 계약도 없으면 하네스 유지보수로 보고 검사하지 않는다."""
        self.make_repo()
        self.write("a.py", "x = 1\n")
        self.commit("feat: 하네스 유지보수")

    def test_main_changes_only_by_merge(self):
        self.git("switch", "-q", "main")
        self.write("a.py", "x = 1\n")
        self.commit("chore: 설정", ok=False, expect="main에 직접 커밋 금지")
        self.git("switch", "-q", "-c", "chore/setting")
        self.commit("chore: 설정")

    def test_approved_ac_needs_user_decision(self):
        """승인 상태는 사용자 승인 decision이 있어야 한다 — 새로 추가한 AC도."""
        self.write("docs/INTENT.md", INTENT_V1)
        self.write("docs/ledger.jsonl", line(type="decision", id="D-1", refs=["AC-1.1"], what="AC 승인",
                                             why="원문 3줄", by="agent"))
        self.commit("docs(intent): 계약", ok=False, expect="[harness guard] AC-1.1 상태가 승인")
        self.write("docs/INTENT.md", INTENT_V1.replace("| 승인 |", "| 가정 |"))
        self.commit("docs(intent): 계약 초안")

    def test_verify_line_needs_rerun_command_and_fills_commit_body(self):
        self.contract()
        self.write("src.py", "x = 1\n")
        self.write("docs/ledger.jsonl", line(type="verify", refs=["AC-1.1"], result="PASS", line="PASS 탐지(R-1)"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1", ok=False, expect="재실행 명령")
        self.git("checkout", "--", "docs/ledger.jsonl")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1")
        body = self.git("log", "-1", "--format=%B").stdout
        self.assertIn("\n\n- PASS 탐지(R-1) — 검증셋 → recall 0.93 (python3 -m pytest -q tests/test_detect.py)", body)

    def test_merge_to_main_needs_every_ac_of_r(self):
        """커밋은 진행(AC 하나 PASS), main 머지는 완료(그 R의 AC 전부 PASS 또는 보류)."""
        self.write("docs/INTENT.md", INTENT_TWO)
        self.write("docs/ledger.jsonl", line(type="decision", id="D-1", refs=["R-1"], what="AC 승인",
                                             why="원문 3줄", by="user"))
        self.commit("docs(intent): 의도 계약 — P-1")
        self.write("src.py", "x = 1\n")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1")
        self.git("switch", "-q", "main")
        r = self.git("merge", "--no-ff", "work", "-m", "merge: work → main")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("AC-1.2", r.stderr)
        self.git("merge", "--abort")
        self.git("switch", "-q", "work")
        self.write("docs/ledger.jsonl", verify("PASS", "AC-1.2"), mode="a")
        self.commit("test(detect): 추론 시간 측정")
        self.git("switch", "-q", "main")
        r = self.git("merge", "--no-ff", "work", "-m", "merge: work → main")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_merge_allows_ac_put_on_hold_by_user(self):
        """끝내지 못한 AC는 사용자 승인으로 보류하면 머지할 수 있다."""
        self.write("docs/INTENT.md", INTENT_TWO)
        self.write("docs/ledger.jsonl", line(type="decision", id="D-1", refs=["R-1"], what="AC 승인",
                                             why="원문 3줄", by="user"))
        self.commit("docs(intent): 의도 계약 — P-1")
        self.write("src.py", "x = 1\n")
        self.write("docs/ledger.jsonl", verify("PASS"), mode="a")
        self.commit("feat(detect): 이상 탐지 — R-1")
        self.write("docs/INTENT.md", INTENT_TWO.replace("추론 1초 이내 | 승인", "추론 1초 이내 | 보류"))
        self.write("docs/ledger.jsonl", line(type="decision", id="D-2", refs=["AC-1.2"], what="승인→보류",
                                             why="시간 부족, 사용자 확인", by="user"), mode="a")
        self.commit("docs(intent): AC-1.2 보류 — D-2")
        self.git("switch", "-q", "main")
        r = self.git("merge", "--no-ff", "work", "-m", "merge: work → main")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_report_shows_trace(self):
        self.contract()
        self.write("docs/ledger.jsonl", line(type="question", id="Q-1", refs=["AC-1.1"], what="오탐 허용치?"), mode="a")
        r = subprocess.run([sys.executable, ".codex/hooks/intent_trace.py", "report"], cwd=self.repo,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertIn("| AC-1.1 | R-1 | docs/task/README.md:3 | D-1 | 미검증 |", r.stdout)
        self.assertIn("열린 질문 Q-1", r.stdout)
        self.assertNotIn("core.hooksPath", r.stdout)
        self.git("config", "--unset", "core.hooksPath")
        r = subprocess.run([sys.executable, ".codex/hooks/intent_trace.py", "report"], cwd=self.repo,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertIn("core.hooksPath=(미설정)", r.stdout)


class ShellGuard(unittest.TestCase):
    def test_denied(self):
        for cmd in ("git commit --no-verify -m x", "git commit -n -m x", "git config --unset core.hooksPath",
                    "git -c core.hooksPath=/dev/null commit -m x", "git config core.hooksPath .git/hooks",
                    "sed -i s/a/b/ docs/task/README.md", "rm docs/task/README.md", "echo x >> docs/task/a.md"):
            self.assertIsNotNone(harness_hook.check_shell(cmd), cmd)

    def test_allowed(self):
        for cmd in ("git config core.hooksPath .codex/hooks/git", "git config --get core.hooksPath",
                    "cp README.md docs/task/README.md", "git commit -m \"feat: x — R-1\"", "git commit --amend --no-edit"):
            self.assertIsNone(harness_hook.check_shell(cmd), cmd)

    def test_patch(self):
        self.assertIsNotNone(harness_hook.check_patch("*** Update File: docs/task/README.md", "."))
        self.assertIsNone(harness_hook.check_patch("*** Add File: docs/task/README.md", "."))


if __name__ == "__main__":
    unittest.main()
