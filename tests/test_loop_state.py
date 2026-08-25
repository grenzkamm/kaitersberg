from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "loop-state.py"
SPEC = importlib.util.spec_from_file_location("loop_state", SCRIPT)
assert SPEC and SPEC.loader
loop_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop_state)


class LoopStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "PROJ-6.json"
        loop_state.initialise(self.path, "PROJ-6", "run-1", "build")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def move(self, stage: str, outcome: str):
        return loop_state.transition(self.path, stage, outcome, "abc123")

    def test_green_path(self) -> None:
        self.assertEqual(self.move("build", "complete")["stage"], "review")
        self.assertEqual(self.move("review", "approved_with_notes")["stage"], "qa")
        self.assertEqual(self.move("qa", "ready_with_reservations")["stage"], "pr")
        result = self.move("pr", "opened")
        self.assertEqual(result["action"], "stop_ok")
        self.assertEqual(result["stage"], "complete")

    def test_findings_return_to_build_and_persist_budget(self) -> None:
        self.move("build", "complete")
        first = self.move("review", "changes_required")
        self.assertEqual((first["stage"], first["attempts"]), ("build", 1))
        self.move("build", "complete")
        second = self.move("review", "changes_required")
        self.assertEqual(second["attempts"], 2)

        reloaded = loop_state.read_state(self.path)
        self.assertEqual(reloaded["attempts"]["review"], 2)

    def test_incomplete_resumes_same_stage(self) -> None:
        result = self.move("build", "incomplete")
        self.assertEqual((result["stage"], result["attempts"]), ("build", 1))

    def test_ci_failure_has_real_return_path(self) -> None:
        self.move("build", "complete")
        self.move("review", "approved")
        self.move("qa", "production_ready")
        result = self.move("pr", "ci_failed")
        self.assertEqual((result["stage"], result["attempts"]), ("build", 1))

    def test_blocked_stops_without_advancing(self) -> None:
        result = self.move("build", "blocked")
        self.assertEqual(result["action"], "stop_blocked")
        self.assertEqual(loop_state.read_state(self.path)["stage"], "build")

    def test_rejects_wrong_stage_and_outcome(self) -> None:
        with self.assertRaises(SystemExit):
            self.move("qa", "production_ready")
        with self.assertRaises(SystemExit):
            self.move("build", "approved")


if __name__ == "__main__":
    unittest.main()
