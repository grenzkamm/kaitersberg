"""loop-status.sh is read-only and tells the loop's five states apart."""

from __future__ import annotations

import os
import subprocess
import unittest
import tempfile
from pathlib import Path


ROOT = Path(__file__).parents[1]
STATUS = ROOT / "scripts" / "loop-status.sh"
STATE_HELPER = ROOT / "scripts" / "loop-state.py"


class LoopStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "product"
        self.repo.mkdir()
        # A pre-commit hook exports GIT_DIR/GIT_INDEX_FILE for the repository being
        # committed. A nested test repository must not inherit that identity.
        self.clean_env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        subprocess.run(
            ["git", "init", "-q", "-b", "main"],
            cwd=self.repo,
            env=self.clean_env,
            check=True,
        )
        self.state_path = self.repo / ".git" / "kaitersberg" / "loops" / "LST-41.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_status(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(STATUS), *args],
            cwd=self.repo,
            env=self.clean_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def state_helper(self, *args: str) -> None:
        subprocess.run(
            ["python3", str(STATE_HELPER), *args],
            env=self.clean_env,
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def init_state(self) -> None:
        self.state_helper(
            "init", str(self.state_path), "LST-41", "run-1", "--rounds", "3"
        )

    def test_repo_without_state_exits_zero_with_a_clear_message(self) -> None:
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no loop state", result.stdout)

    def test_unknown_feature_exits_zero_with_a_clear_message(self) -> None:
        result = self.run_status("LST-9")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no loop state for LST-9", result.stdout)

    def test_snapshot_shows_stage_round_and_stale_without_a_process(self) -> None:
        self.init_state()
        result = self.run_status("LST-41")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("LST-41", result.stdout)
        self.assertIn("build (round 1/3)", result.stdout)
        self.assertIn("stale", result.stdout)
        self.assertIn("none", result.stdout)
        self.assertIn("not held", result.stdout)

    def test_blocked_state_reads_as_decision_needed(self) -> None:
        self.init_state()
        self.state_helper("transition", str(self.state_path), "build", "blocked")
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stopped: decision needed", result.stdout)

    def test_exhausted_budget_reads_as_rounds_exhausted(self) -> None:
        self.init_state()
        for outcome in ("incomplete", "incomplete", "incomplete"):
            self.state_helper("transition", str(self.state_path), "build", outcome)
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stopped: rounds exhausted", result.stdout)

    def test_status_is_read_only(self) -> None:
        self.init_state()
        before = self.state_path.read_text(encoding="utf-8")
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state_path.read_text(encoding="utf-8"), before)
        self.assertFalse((self.state_path.parent / "LST-41.lock").exists())


if __name__ == "__main__":
    unittest.main()
