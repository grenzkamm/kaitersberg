"""loop-status.sh is read-only and tells the loop's five states apart."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
STATUS = ROOT / "scripts" / "loop-status.sh"
BUNDLED_STATUS = (
    ROOT
    / ".claude"
    / "skills"
    / "build-loop"
    / "scripts"
    / "loop-status.sh"
)
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

    def run_status(
        self, *args: str, status_path: Path = STATUS
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(status_path), *args],
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

    def test_bundled_status_operates_from_a_foreign_product_repo(self) -> None:
        result = self.run_status(status_path=BUNDLED_STATUS)

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

    def test_global_snapshot_unions_state_and_detached_only_features(self) -> None:
        self.init_state()
        state_dir = self.state_path.parent
        state_launcher = state_dir / "LST-41-20260101T000000Z-1.detached.log"
        state_launcher.write_text("state-backed launcher\n", encoding="utf-8")
        state_launcher.with_suffix(".exit").write_text("0\n", encoding="utf-8")
        for timestamp, code in (("20260101T000000Z-1", 64), ("20260102T000000Z-2", 65)):
            launcher = state_dir / f"LST-42-{timestamp}.detached.log"
            launcher.write_text("detached-only launcher\n", encoding="utf-8")
            launcher.with_suffix(".exit").write_text(f"{code}\n", encoding="utf-8")

        result = self.run_status()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("LST-41  stale"), 1)
        self.assertEqual(
            result.stdout.count("LST-42  detached launcher exited 65"), 1
        )
        self.assertNotIn("LST-42  detached launcher exited 64", result.stdout)

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

    def test_bug_3_same_feature_process_from_another_repo_is_not_running(self) -> None:
        self.init_state()
        foreign = subprocess.Popen(
            ["bash", "-c", "sleep 5 & wait", "loop-feature.sh", "LST-41"],
            env=self.clean_env,
            start_new_session=True,
        )
        try:
            time.sleep(0.1)
            result = self.run_status("LST-41")
        finally:
            os.killpg(foreign.pid, signal.SIGTERM)
            foreign.wait(timeout=1)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stale: no loop process", result.stdout)
        self.assertIn("process     none", result.stdout)

    def test_repository_pid_file_identifies_the_running_loop(self) -> None:
        self.init_state()
        (self.state_path.parent / "LST-41.lock").mkdir()
        local = subprocess.Popen(
            ["bash", "-c", "sleep 5 & wait", "loop-feature.sh", "LST-41"],
            env=self.clean_env,
            start_new_session=True,
        )
        (self.state_path.parent / "LST-41.pid").write_text(
            f"{local.pid}\n", encoding="utf-8"
        )
        try:
            time.sleep(0.1)
            result = self.run_status("LST-41")
        finally:
            os.killpg(local.pid, signal.SIGTERM)
            local.wait(timeout=1)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("LST-41  running", result.stdout)
        self.assertIn(f"process     pid {local.pid} alive", result.stdout)


if __name__ == "__main__":
    unittest.main()
