"""Exercise the project-specific verification hook without installing app packages."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "Bash and Git required")
class VerifyLocalTests(unittest.TestCase):
    def test_non_executable_local_check_runs_and_propagates_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / ".harness/bin"
            binary.mkdir(parents=True)
            shutil.copy2(REPO / ".harness/bin/verify.sh", binary / "verify.sh")
            # Isolate the extension contract from Python discovery and optional packages.
            python_path = Path(sys.executable).as_posix().replace("'", "'\"'\"'")
            (binary / "runtime.sh").write_text(f"PY='{python_path}'\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            local = root / ".harness/verify.local.sh"
            environment = {**os.environ, "PYTHONUTF8": "1"}
            for code in (7, 0):
                with self.subTest(exit_code=code):
                    local.write_text(f"echo local-check-ran\nexit {code}\n", encoding="utf-8")
                    local.chmod(0o644)
                    result = subprocess.run(
                        [shutil.which("bash"), ".harness/bin/verify.sh"], cwd=root,
                        env=environment, capture_output=True, encoding="utf-8",
                        errors="replace", timeout=30,
                    )
                    self.assertEqual(result.returncode, int(code != 0), result.stdout + result.stderr)
                    self.assertIn(("FAIL" if code else "PASS") + "  프로젝트 전용 검증", result.stdout)
                    if code:
                        self.assertIn("local-check-ran", result.stdout)


if __name__ == "__main__":
    unittest.main()
