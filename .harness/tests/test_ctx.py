"""Tests for .harness/bin/ctx.py and the hook's ctx/ injection (run: python3 -m unittest discover tests)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CTX = REPO / ".harness" / "bin" / "ctx.py"
HOOK = REPO / ".codex" / "hooks" / "harness_hook.py"

REPORT = "# r\n## 결론\n- IsolationForest 우선\n## 근거\n- [사실] profile.md:3\n## 미확인\n없음\n"


class CtxBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "ws"
        self.ws.mkdir()
        self.env = {**os.environ, "CTX_ROOT": str(self.ws), "PYTHONIOENCODING": "utf-8"}

    def tearDown(self):
        self.tmp.cleanup()

    def ctx(self, *args):
        p = subprocess.run([sys.executable, str(CTX), *args], capture_output=True, env=self.env, timeout=30)
        return p.returncode, p.stdout.decode("utf-8")

    def write(self, rel, text):
        p = self.ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def research(self, slug="anomaly", inputs=()):
        args = ["new", "research", slug, "--q", "이상치 탐지 방법 비교", "--serves", "R-2"]
        if inputs:
            args += ["--inputs", *[str(self.ws / i) for i in inputs]]
        self.assertEqual(self.ctx(*args)[0], 0)
        self.write(f"ctx/research/{slug}/report.md", REPORT)
        self.assertEqual(self.ctx("done", f"research/{slug}")[0], 0)


class Lifecycle(CtxBase):
    def test_done_rejects_empty_template(self):
        self.ctx("new", "research", "anomaly", "--q", "q")
        rc, out = self.ctx("done", "research/anomaly")
        self.assertEqual(rc, 1)
        self.assertIn("결론", out)
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "draft")

    def test_done_derives_summary_and_indexes(self):
        self.research()
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "valid")
        index = (self.ws / "ctx" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("IsolationForest 우선", index)
        self.assertIn("R-2", index)

    def test_new_on_valid_refuses_without_redo(self):
        self.research()
        rc, out = self.ctx("new", "research", "anomaly", "--q", "again")
        self.assertEqual(rc, 3)
        self.assertIn("재사용", out)
        rc, _ = self.ctx("new", "research", "anomaly", "--redo")
        self.assertEqual(rc, 0)
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "draft")
        self.assertTrue((self.ws / "ctx/research/anomaly/_prev/report.md").exists())

    def test_bad_slug_and_kind(self):
        self.assertEqual(self.ctx("new", "research", "Bad Slug", "--q", "q")[0], 2)
        self.assertEqual(self.ctx("new", "wiki", "x", "--q", "q")[0], 2)
        self.assertEqual(self.ctx("new", "research", "x")[0], 2)  # --q required for a new entry

    def test_find_matches_korean_with_particles(self):
        self.research()
        rc, out = self.ctx("find", "이상치를", "찾아줘")
        self.assertIn("research/anomaly", out)
        rc, out = self.ctx("find", "대시보드")
        self.assertIn("관련 기록 없음", out)

    def test_corrupt_line_is_skipped(self):
        self.research()
        with open(self.ws / "ctx" / "index.jsonl", "a", encoding="utf-8") as f:
            f.write("{not json\n")
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "valid")


class Freshness(CtxBase):
    def test_input_change_makes_stale(self):
        self.write("data.csv", "a,b\n1,2\n")
        self.research(inputs=["data.csv"])
        self.write("data.csv", "a,b\n1,3\n9,9\n")
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "stale")
        _, out = self.ctx("get", "research/anomaly")
        self.assertIn("입력 변경: data.csv", out)

    def test_missing_input_refuses_done(self):
        self.ctx("new", "research", "anomaly", "--q", "q", "--inputs", str(self.ws / "nope.csv"))
        self.write("ctx/research/anomaly/report.md", REPORT)
        rc, out = self.ctx("done", "research/anomaly")
        self.assertEqual(rc, 1)
        self.assertIn("nope.csv", out)

    def test_dependency_redo_makes_dependent_stale(self):
        self.research()
        self.ctx("new", "decision", "method", "--q", "방법 선정", "--uses", "research/anomaly")
        self.write("ctx/decision/method/decision.md", "## 결정\nIF\n## 버린 대안\n3σ\n## 근거 대조\nok\n")
        self.assertEqual(self.ctx("done", "decision/method")[0], 0)
        self.assertEqual(self.ctx("state", "decision/method")[1].strip(), "valid")
        self.ctx("new", "research", "anomaly", "--redo")
        self.assertEqual(self.ctx("state", "decision/method")[1].strip(), "stale")
        self.write("ctx/research/anomaly/report.md", REPORT)
        self.ctx("done", "research/anomaly")  # redone: decision was built on the old version
        _, out = self.ctx("get", "decision/method")
        self.assertIn("갱신됨", out)

    def test_done_refuses_when_dependency_not_valid(self):
        self.ctx("new", "research", "anomaly", "--q", "q")
        self.ctx("new", "decision", "method", "--q", "q", "--uses", "research/anomaly")
        self.write("ctx/decision/method/decision.md", "## 결정\nIF\n## 버린 대안\nx\n## 근거 대조\nok\n")
        self.assertEqual(self.ctx("done", "decision/method")[0], 1)

    def test_superseded_and_manual_valid_blocked(self):
        self.research()
        self.research("anomaly-v2")
        self.assertEqual(self.ctx("status", "research/anomaly", "superseded", "--by", "research/anomaly-v2")[0], 0)
        self.assertEqual(self.ctx("state", "research/anomaly")[1].strip(), "superseded")
        self.assertEqual(self.ctx("status", "research/anomaly", "valid")[0], 2)

    def test_check_reports_and_flags_broken_valid_body(self):
        self.research()
        self.write("ctx/research/anomaly/report.md", "# emptied\n")
        rc, out = self.ctx("check")
        self.assertEqual(rc, 1)
        self.assertIn("본문 문제", out)


class HookInjection(CtxBase):
    def hook(self, mode, payload):
        home = Path(self.tmp.name) / "state"
        home.mkdir(exist_ok=True)
        (home / "workspace").write_text(str(self.ws), encoding="utf-8")
        env = {**self.env, "HYNIX_HARNESS_HOME": str(home), "HYNIX_HARNESS_NOLOG": "1"}
        p = subprocess.run([sys.executable, str(HOOK), mode], input=json.dumps(payload).encode(),
                           capture_output=True, env=env, timeout=20)
        out = p.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def test_session_start_lists_entries(self):
        self.research()
        out = self.hook("session-start", {"source": "startup", "cwd": str(self.ws)})
        text = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("research/anomaly [valid] IsolationForest 우선", text)
        self.assertIn("ctx.py find", text)

    def test_prompt_injects_only_related(self):
        self.research()
        out = self.hook("prompt", {"model": "gpt-6.1-sol", "prompt": "이상치 탐지 방법을 조사해줘", "cwd": str(self.ws)})
        self.assertIn("research/anomaly", out["hookSpecificOutput"]["additionalContext"])
        out = self.hook("prompt", {"model": "gpt-6.1-sol", "prompt": "서버 포트 확인", "cwd": str(self.ws)})
        self.assertIsNone(out)

    def test_no_ctx_folder_is_silent(self):
        out = self.hook("session-start", {"source": "startup", "cwd": str(self.ws)})
        self.assertIsNone(out)

    def test_direct_index_edit_denied(self):
        for payload in ({"tool_name": "Bash", "tool_input": {"command": "echo '{}' >> ctx/index.jsonl"}},
                        {"tool_name": "apply_patch", "tool_input": {"command":
                            "*** Begin Patch\n*** Update File: ctx/index.jsonl\n@@\n-a\n+b\n*** End Patch\n"}}):
            with self.subTest(tool=payload["tool_name"]):
                out = self.hook("pretool", {**payload, "cwd": str(self.ws)})
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        allowed = {"tool_name": "Bash", "tool_input": {"command": "cat ctx/index.jsonl"}, "cwd": str(self.ws)}
        self.assertIsNone(self.hook("pretool", allowed))


if __name__ == "__main__":
    unittest.main()
