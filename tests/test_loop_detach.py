"""Detached delivery keeps early runner failures observable."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
DETACH = (
    ROOT
    / ".claude"
    / "skills"
    / "build-loop"
    / "scripts"
    / "loop-detach.sh"
)
STATUS = DETACH.with_name("loop-status.sh")

FAKE_TMUX = r'''#!/usr/bin/env python3
import subprocess
import sys

if len(sys.argv) > 1 and sys.argv[1] == "has-session":
    raise SystemExit(1)
if len(sys.argv) > 1 and sys.argv[1] == "new-session":
    subprocess.Popen(
        ["/bin/sh", "-c", sys.argv[-1]],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    raise SystemExit(0)
raise SystemExit(64)
'''


class DetachedLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "product"
        self.bin = self.root / "bin"
        self.repo.mkdir()
        self.bin.mkdir()
        self.clean_env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        subprocess.run(
            ["git", "init", "-q", "-b", "main"],
            cwd=self.repo,
            env=self.clean_env,
            check=True,
        )
        (self.repo / "features" / "PROJ-7-example").mkdir(parents=True)
        tmux = self.bin / "tmux"
        tmux.write_text(FAKE_TMUX, encoding="utf-8")
        tmux.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def output_path(output: str, label: str) -> Path:
        prefix = f"{label}: "
        line = next(line for line in output.splitlines() if line.startswith(prefix))
        return Path(line.removeprefix(prefix))

    def test_immediate_runner_failure_keeps_output_and_exit_code(self) -> None:
        env = self.clean_env.copy()
        env.update(
            PATH=f"{self.bin}:{env['PATH']}",
            KAITERSBERG_HARNESS="not-a-harness",
        )

        result = subprocess.run(
            ["bash", str(DETACH), "PROJ-7"],
            cwd=self.repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("accepted; current state unknown", result.stdout)
        capture = self.output_path(result.stdout, "launcher log")
        exit_file = self.output_path(result.stdout, "launcher exit")
        deadline = time.monotonic() + 2
        while not exit_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)

        self.assertEqual(exit_file.read_text(encoding="utf-8").strip(), "64")
        self.assertIn(
            "invalid KAITERSBERG_HARNESS=not-a-harness",
            capture.read_text(encoding="utf-8"),
        )
        self.assertFalse(
            (self.repo / ".git" / "kaitersberg" / "loops" / "PROJ-7.json").exists()
        )
        self.assertFalse(
            (self.repo / "features" / "PROJ-7-example" / "loop.log").exists()
        )

        status = subprocess.run(
            ["bash", str(STATUS), "PROJ-7"],
            cwd=self.repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("detached launcher exited 64", status.stdout)
        self.assertIn(f"launcher log   {capture}", status.stdout)

        global_status = subprocess.run(
            ["bash", str(STATUS)],
            cwd=self.repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(global_status.returncode, 0, global_status.stderr)
        self.assertIn("PROJ-7  detached launcher exited 64", global_status.stdout)
        self.assertIn(f"launcher log   {capture}", global_status.stdout)
        self.assertNotIn("no unattended run has started here", global_status.stdout)


if __name__ == "__main__":
    unittest.main()
