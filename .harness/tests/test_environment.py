"""Behavioral tests for setup and overlay installation; no network or model calls."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
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
overlay = load("install_workspace")


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

    def test_installed_packages_skip_venv_and_pip(self):
        with patch.object(env, "import_ok", return_value=True), patch.object(env, "run") as run, patch.object(env.subprocess, "call") as call:
            self.assertEqual(env.install(["data"]), Path(sys.executable))
            run.assert_not_called()
            call.assert_not_called()
        self.assertFalse((self.root / ".venv").exists())

    def test_install_only_missing_selected_packages(self):
        python = self.file(".venv/" + ("Scripts/python.exe" if env.os.name == "nt" else "bin/python3"))
        installed = False
        def available(interpreter, module):
            return module != "openpyxl" or installed
        def pip(args, **kwargs):
            nonlocal installed
            self.assertEqual(args, [str(python), "-m", "pip", "--disable-pip-version-check", "install", "openpyxl"])
            installed = True
            return 0
        with patch.object(env, "import_ok", side_effect=available), patch.object(env, "run", side_effect=self.fake_run), patch.object(env.subprocess, "call", side_effect=pip) as call:
            self.assertEqual(env.install(["excel"]), python)
            self.assertEqual(call.call_count, 1)

    def test_failed_install_stops(self):
        self.file(".venv/" + ("Scripts/python.exe" if env.os.name == "nt" else "bin/python3"))
        with patch.object(env, "import_ok", return_value=False), patch.object(env, "run", side_effect=self.fake_run), patch.object(env.subprocess, "call", return_value=1):
            self.assertIsNone(env.install(["verify"]))
        self.assertFalse((self.root / ".harness/requirements.local.txt").exists())

    def test_initialize_is_idempotent_and_keeps_ignore_rules(self):
        self.file(".gitignore", "provided-data/\n")
        self.file(".harness/bin/test.sh", "#!/usr/bin/env bash\n")
        with patch.object(env, "run", side_effect=self.fake_run):
            self.assertTrue(env.initialize())
            before = (self.root / ".gitignore").read_text()
            self.assertTrue(env.initialize())
        self.assertEqual((self.root / ".gitignore").read_text(), before)
        self.assertIn("provided-data/", before)

    def test_overlay_preserves_task_files_and_reports_conflicts(self):
        self.file("README.md", "original task")
        self.file("AGENTS.md", "organizer instructions")
        with patch.object(sys, "argv", ["bootstrap", str(self.root)]), patch.object(overlay.subprocess, "call", return_value=0):
            self.assertEqual(overlay.main(), 1)
            self.assertEqual(overlay.main(), 1)
        self.assertEqual((self.root / "README.md").read_text(), "original task")
        self.assertEqual((self.root / "AGENTS.md").read_text(), "organizer instructions")
        self.assertTrue((self.root / "AGENTS.harness.md").exists())
        self.assertTrue((self.root / ".agents/skills/research/SKILL.md").exists())
        self.assertFalse((self.root / "tests").exists())


if __name__ == "__main__":
    unittest.main()
