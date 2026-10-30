"""Behavioral tests for the environment check; no network or model calls."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / f".harness/bin/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


env = load("environment")


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / ".harness").mkdir()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(patch.stopall)
        patch.object(env, "ROOT", self.root).start()
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def file(self, relative, content=""):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def fixture(self):
        for relative in ("AGENTS.md", ".codex/config.toml", ".codex/hooks/harness_hook.py",
                         ".codex/rules/harness.rules", "prompts/SCRIPT.md"):
            self.file(relative)
        for skill in env.SKILLS:
            self.file(f".agents/skills/{skill}/SKILL.md", f"---\nname: {skill}\ndescription: test\n---\n")
        for agent in env.AGENTS:
            self.file(f".codex/agents/{agent}.toml")
        self.file(".codex/hooks.json", json.dumps({"hooks": {key: [] for key in ("SessionStart", "UserPromptSubmit", "PreToolUse")}}))

    def fake_run(self, args, **kwargs):
        out = "version 1\n"
        if "--show-toplevel" in args:
            out = str(self.root)
        if args[-1] == "pretool":
            command = json.loads(kwargs["input"])["tool_input"]["command"]
            out = '' if command.startswith("python3") else '{"permissionDecision":"deny"}'
        return subprocess.CompletedProcess(args, 0, out, "")

    def test_check_is_read_only_and_optional_packages_not_required(self):
        self.fixture()
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch.object(env, "run", side_effect=self.fake_run), patch.object(env, "import_ok") as imports:
            self.assertEqual(env.check([]), 0)
            imports.assert_not_called()
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_broken_executable_fails_even_when_command_exists(self):
        self.fixture()
        def broken(args, **kwargs):
            if args[0] == "codex":
                return subprocess.CompletedProcess(args, 9, "", "broken executable")
            return self.fake_run(args, **kwargs)
        with patch.object(env, "run", side_effect=broken):
            self.assertEqual(env.check([]), 1)

    def test_missing_one_skill_fails(self):
        self.fixture()
        (self.root / ".agents/skills/research/SKILL.md").unlink()
        with patch.object(env, "run", side_effect=self.fake_run):
            self.assertEqual(env.check([]), 1)

    def test_selected_missing_dependency_fails(self):
        self.fixture()
        with patch.object(env, "run", side_effect=self.fake_run), patch.object(env, "import_ok", return_value=False):
            self.assertEqual(env.check(["parquet"]), 1)

    def test_frontend_runtime_is_checked(self):
        self.fixture()
        self.file("frontend/package.json", "{}")

        def missing_npm(args, **kwargs):
            if args[0] == "npm":
                return subprocess.CompletedProcess(args, 1, "", "npm unavailable")
            return self.fake_run(args, **kwargs)

        with patch.object(env, "run", side_effect=missing_npm) as calls:
            self.assertEqual(env.check([]), 1)
        self.assertTrue(any(call.args[0] == ["node", "--version"] for call in calls.call_args_list))
        self.assertIn("npm", self.output.getvalue())

    def test_missing_fe_skill_fails(self):
        self.fixture()
        (self.root / ".agents/skills/fe-build/SKILL.md").unlink()
        with patch.object(env, "run", side_effect=self.fake_run):
            self.assertEqual(env.check([]), 1)


if __name__ == "__main__":
    unittest.main()
