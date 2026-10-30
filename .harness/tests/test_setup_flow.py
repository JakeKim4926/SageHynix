"""Exercise real Bash/Python setup in a temporary workspace with a version-only Codex stub."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "Bash and Git required")
class SetupFlow(unittest.TestCase):
    def test_overlay_setup_rerun_and_readonly_doctor(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            workspace = base / "task with spaces"
            workspace.mkdir()
            (workspace / "README.md").write_text("organizer task", encoding="utf-8")
            binary = base / "bin"
            binary.mkdir()
            stub = binary / ("codex.cmd" if os.name == "nt" else "codex")
            stub.write_text("@echo off\necho codex-test-version\n" if os.name == "nt" else "#!/bin/sh\necho codex-test-version\n", encoding="utf-8")
            stub.chmod(0o755)
            environment = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                           "PYTHONUTF8": "1", "HYNIX_HARNESS_HOME": str(base / "state")}

            def call(script, *args, cwd=REPO):
                result = subprocess.run([shutil.which("bash"), script, *args], cwd=cwd, env=environment,
                                        capture_output=True, encoding="utf-8", errors="replace", timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            call("bootstrap.sh", str(workspace))
            self.assertEqual((workspace / "README.md").read_text(), "organizer task")
            self.assertTrue((workspace / "prompts/SCRIPT.md").exists())
            self.assertTrue((workspace / "docs/research").is_dir())
            agents = workspace / "AGENTS.md"
            original_agents = agents.read_bytes()
            call("bootstrap.sh", str(workspace))
            call("setup.sh", cwd=workspace)
            self.assertEqual(agents.read_bytes(), original_agents)
            before = {str(p): p.read_bytes() for p in workspace.rglob("*") if p.is_file() and ".git" not in p.parts}
            output = call(".harness/bin/doctor.sh", cwd=workspace)
            self.assertIn("codex-test-version", output)
            after = {str(p): p.read_bytes() for p in workspace.rglob("*") if p.is_file() and ".git" not in p.parts}
            self.assertEqual(before, after)
            result = subprocess.run(["git", "-C", str(workspace), "rev-parse", "--verify", "HEAD"], capture_output=True)
            self.assertNotEqual(result.returncode, 0, "setup must not auto-commit")
            # A new terminal in a worktree must resolve the same shared state directory without a global home file.
            subprocess.run(["git", "-C", str(workspace), "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(workspace), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "temporary harness fixture"], check=True, capture_output=True)
            lane = base / "lane"
            subprocess.run(["git", "-C", str(workspace), "worktree", "add", "-b", "test-lane", str(lane)], check=True, capture_output=True)
            environment.pop("HYNIX_HARNESS_HOME", None)
            probe = 'source .harness/bin/runtime.sh; printf "%s\\n" "$HYNIX_HARNESS_HOME" "$PY"'
            self.assertEqual(call("-c", probe, cwd=workspace), call("-c", probe, cwd=lane))


if __name__ == "__main__":
    unittest.main()
