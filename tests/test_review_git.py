from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
HELPER = ROOT / "scripts" / "review-git.py"


class ReviewGitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / "sample.txt").write_text("first\n", encoding="utf-8")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "first")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        (self.repo / "sample.txt").write_text("second\n", encoding="utf-8")
        self.git("commit", "-qam", "second")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repo,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def helper(self, *arguments: str, **env: str) -> subprocess.CompletedProcess[str]:
        run_env = self.env | env
        return subprocess.run(
            [str(HELPER), "--repo", str(self.repo), *arguments],
            env=run_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_exposes_diff_and_status_without_refreshing_the_index(self) -> None:
        diff = self.helper("diff", self.base, "HEAD")
        self.assertEqual(diff.returncode, 0, diff.stderr)
        self.assertIn("-first", diff.stdout)
        self.assertIn("+second", diff.stdout)
        self.assertEqual(self.helper("status").returncode, 0)

    def test_rejects_git_options_as_revisions(self) -> None:
        result = self.helper("diff", "--output=sample.txt", "HEAD")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "sample.txt").read_text(encoding="utf-8"), "second\n")

    def test_disables_external_diff_commands(self) -> None:
        marker = Path(self.temporary.name) / "external-diff-ran"
        fsmonitor_marker = Path(self.temporary.name) / "fsmonitor-ran"
        fsmonitor = Path(self.temporary.name) / "fsmonitor"
        fsmonitor.write_text(f"#!/bin/sh\ntouch {fsmonitor_marker}\n", encoding="utf-8")
        fsmonitor.chmod(0o755)
        (self.repo / ".gitattributes").write_text("*.txt diff=hostile\n", encoding="utf-8")
        self.git("add", ".gitattributes")
        self.git("commit", "-qm", "attributes")
        self.git("config", "diff.hostile.command", f"touch {marker}")
        self.git("config", "core.fsmonitor", str(fsmonitor))

        result = self.helper("diff", self.base, "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.helper("status").returncode, 0)
        self.assertFalse(marker.exists())
        self.assertFalse(fsmonitor_marker.exists())

    def test_ignores_ambient_repository_identity(self) -> None:
        other = Path(self.temporary.name) / "other"
        other.mkdir()
        subprocess.run(
            ["git", "init", "-q"], cwd=other, env=self.env, check=True
        )
        result = self.helper("rev-parse", "show-toplevel", GIT_DIR=str(other / ".git"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.repo.resolve())


if __name__ == "__main__":
    unittest.main()
