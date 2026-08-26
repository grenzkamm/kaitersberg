from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
LOOP = ROOT / "scripts" / "loop-feature.sh"
BUNDLED_LOOP = (
    ROOT
    / ".claude"
    / "skills"
    / "build-loop"
    / "scripts"
    / "loop-feature.sh"
)
BUILD_SKILL = ROOT / ".claude" / "skills" / "build" / "SKILL.md"


FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import time

queue = Path(os.environ["FAKE_CLAUDE_QUEUE"])
items = queue.read_text(encoding="utf-8").splitlines()
outcome = items.pop(0) if items else ""
queue.write_text("\n".join(items) + ("\n" if items else ""), encoding="utf-8")
calls = Path(os.environ["FAKE_CLAUDE_CALLS"])
calls.write_text(calls.read_text(encoding="utf-8") + outcome + "\n", encoding="utf-8")
with Path(os.environ["FAKE_CLAUDE_ARGS"]).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\n")
if outcome == "rate_limited":
    child_pid_path = os.environ.get("FAKE_RATE_LIMIT_CHILD_PID")
    if child_pid_path:
        child_ready_path = os.environ["FAKE_RATE_LIMIT_CHILD_READY"]
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import signal, sys, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "open(sys.argv[1], 'w').write('ready'); "
                "time.sleep(60)",
                child_ready_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        Path(child_pid_path).write_text(str(child.pid), encoding="utf-8")
        deadline = time.monotonic() + 2
        while not Path(child_ready_path).exists() and time.monotonic() < deadline:
            time.sleep(0.01)
    print(json.dumps({
        "type": "rate_limit_event",
        "session_id": "session-rate-limited",
        "rate_limit_info": {"status": "rejected", "resetsAt": 1787756400},
    }), flush=True)
    time.sleep(float(os.environ.get("FAKE_RATE_LIMIT_SLEEP", "10")))
    raise SystemExit(99)
structured = {"outcome": outcome, "head_sha": "abc1234"} if outcome else None
if structured and outcome == "blocked":
    structured["reason"] = "which provider owns login"
print(json.dumps({
    "type": "result", "subtype": "success", "session_id": f"session-{outcome}",
    "num_turns": 1, "duration_ms": 10, "total_cost_usd": 0,
    "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0},
    "structured_output": structured,
}))
'''

FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

queue = Path(os.environ["FAKE_CODEX_QUEUE"])
items = queue.read_text(encoding="utf-8").splitlines()
outcome = items.pop(0) if items else ""
queue.write_text("\n".join(items) + ("\n" if items else ""), encoding="utf-8")
args = sys.argv[1:]
prompt = args[-1] if args else ""
structured = {"outcome": outcome, "head_sha": "abc1234"} if outcome else None
calls = Path(os.environ["FAKE_CODEX_CALLS"])
with calls.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({"args": args, "prompt": prompt, "outcome": outcome}) + "\n")
if structured and "--output-last-message" in args:
    output = Path(args[args.index("--output-last-message") + 1])
    output.write_text(json.dumps(structured), encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": f"thread-{outcome}"}))
if structured:
    print(json.dumps({
        "type": "item.completed",
        "item": {"id": "item-1", "type": "agent_message", "text": json.dumps(structured)},
    }))
print(json.dumps({
    "type": "turn.completed",
    "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1},
}))
'''

FAKE_HOOK = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path

state = json.loads(Path(os.environ["HOOK_STATE"]).read_text(encoding="utf-8"))
payload = {
    key: os.environ.get(key)
    for key in ("STAGE", "OUTCOME", "FEATURE", "RUN_ID", "HEAD_SHA", "NEXT_STAGE", "ACTION")
}
payload["persisted_stage"] = state["stage"]
path = Path(os.environ["HOOK_LOG"])
with path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(payload) + "\n")
raise SystemExit(int(os.environ.get("HOOK_EXIT", "0")))
'''

FAKE_NOTIFY = r'''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

with Path(os.environ["NOTIFY_LOG"]).open("a", encoding="utf-8") as handle:
    handle.write("\t".join(sys.argv[1:]) + "\n")
raise SystemExit(int(os.environ.get("NOTIFY_EXIT", "0")))
'''


class FeatureLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "product"
        self.bin = self.root / "bin"
        # A pre-commit hook exports GIT_DIR/GIT_INDEX_FILE for the repository being
        # committed. A nested test repository must not inherit that identity.
        self.clean_env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        self.repo.mkdir()
        self.bin.mkdir()
        subprocess.run(
            ["git", "init", "-q", "-b", "main"],
            cwd=self.repo,
            env=self.clean_env,
            check=True,
        )
        (self.repo / "features" / "PROJ-7-example").mkdir(parents=True)
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        fake.chmod(0o755)
        fake_codex = self.bin / "codex"
        fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        fake_codex.chmod(0o755)
        self.queue = self.root / "queue"
        self.calls = self.root / "calls"
        self.calls.write_text("", encoding="utf-8")
        self.claude_args = self.root / "claude-args"
        self.claude_args.write_text("", encoding="utf-8")
        self.codex_calls = self.root / "codex-calls"
        self.codex_calls.write_text("", encoding="utf-8")
        self.hook_log = self.root / "hook-log"
        self.hook_log.write_text("", encoding="utf-8")
        self.hook = self.bin / "hook"
        self.hook.write_text(FAKE_HOOK, encoding="utf-8")
        self.hook.chmod(0o755)
        self.notify_log = self.root / "notify-log"
        self.notify_log.write_text("", encoding="utf-8")
        self.notifier = self.bin / "notifier"
        self.notifier.write_text(FAKE_NOTIFY, encoding="utf-8")
        self.notifier.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_loop(
        self,
        outcomes: list[str],
        timeout: float | None = None,
        loop_path: Path = LOOP,
        **extra: str,
    ) -> subprocess.CompletedProcess[str]:
        self.queue.write_text("\n".join(outcomes) + "\n", encoding="utf-8")
        env = self.clean_env.copy()
        env.update(
            PATH=f"{self.bin}:{env['PATH']}",
            FAKE_CLAUDE_QUEUE=str(self.queue),
            FAKE_CLAUDE_CALLS=str(self.calls),
            FAKE_CLAUDE_ARGS=str(self.claude_args),
            FAKE_CODEX_QUEUE=str(self.queue),
            FAKE_CODEX_CALLS=str(self.codex_calls),
            INFRA_RETRIES="0",
            KAITERSBERG_HARNESS="claude",
        )
        env.update(extra)
        return subprocess.run(
            ["bash", str(loop_path), "PROJ-7"],
            cwd=self.repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )

    def path_without_timeout(self) -> str:
        isolated = self.root / "no-timeout-bin"
        isolated.mkdir()
        for command in (
            "bash",
            "date",
            "dirname",
            "git",
            "jq",
            "mkdir",
            "mktemp",
            "rm",
            "rmdir",
            "sleep",
            "tail",
            "tee",
            "wc",
        ):
            target = shutil.which(command)
            if target is None:
                self.fail(f"test prerequisite is missing: {command}")
            os.symlink(target, isolated / command)
        os.symlink(sys.executable, isolated / "python3")
        os.symlink(self.bin / "claude", isolated / "claude")
        return str(isolated)

    def state_path(self) -> Path:
        return self.repo / ".git" / "kaitersberg" / "loops" / "PROJ-7.json"

    def state(self) -> dict:
        return json.loads(self.state_path().read_text(encoding="utf-8"))

    @staticmethod
    def process_exists(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def hook_env(self, **extra: str) -> dict[str, str]:
        return {
            "STAGE_DONE_CMD": str(self.hook),
            "HOOK_STATE": str(self.repo / ".git" / "kaitersberg" / "loops" / "PROJ-7.json"),
            "HOOK_LOG": str(self.hook_log),
            **extra,
        }

    def test_green_path_preserves_nonblocking_outcomes(self) -> None:
        result = self.run_loop(
            ["complete", "approved_with_notes", "ready_with_reservations", "opened"]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["stage"], "complete")
        self.assertEqual(len(self.calls.read_text(encoding="utf-8").splitlines()), 4)
        self.assertFalse((self.state_path().parent / "PROJ-7.pid").exists())
        self.assertIn(f"state: {self.state_path().resolve()}", result.stdout)
        self.assertIn(
            "events: "
            f"{(self.repo / 'features' / 'PROJ-7-example' / 'loop.log').resolve()}",
            result.stdout,
        )

    def test_bundled_runner_operates_from_a_foreign_product_repo(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready", "opened"],
            loop_path=BUNDLED_LOOP,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["stage"], "complete")

    def test_codex_runner_drives_each_stage_with_codex_exec(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready", "opened"],
            KAITERSBERG_HARNESS="codex",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [
            json.loads(line)
            for line in self.codex_calls.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual([call["outcome"] for call in calls], [
            "complete", "approved", "production_ready", "opened"
        ])
        self.assertEqual(
            [call["prompt"].split()[0] for call in calls],
            [
                "$kaitersberg:build",
                "$kaitersberg:review",
                "$kaitersberg:qa",
                "$kaitersberg:pr",
            ],
        )
        self.assertTrue(all("--json" in call["args"] for call in calls))
        self.assertTrue(all("--ephemeral" in call["args"] for call in calls))
        self.assertTrue(all("workspace-write" in call["args"] for call in calls))
        self.assertTrue(all("--output-schema" in call["args"] for call in calls))
        self.assertTrue(all("--output-last-message" in call["args"] for call in calls))

    def test_parent_codex_session_selects_codex_runner_automatically(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready"],
            KAITERSBERG_HARNESS="auto",
            CODEX_SESSION_ID="parent-codex-session",
            PR="0",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.codex_calls.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.calls.read_text(encoding="utf-8"), "")

    def test_build_skill_redirects_whole_delivery_to_the_runner(self) -> None:
        instructions = BUILD_SKILL.read_text(encoding="utf-8")
        self.assertIn("/build-loop PROJ-x", instructions)
        self.assertIn("Never synthesise the delivery loop inside this session", instructions)

    def test_changes_required_returns_to_build(self) -> None:
        result = self.run_loop(
            [
                "complete",
                "changes_required",
                "complete",
                "approved",
                "production_ready",
                "opened",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["attempts"]["review"], 1)

    def test_pr_zero_resumes_at_pr_without_noop_build(self) -> None:
        first = self.run_loop(
            ["complete", "approved", "production_ready"], PR="0"
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(self.state()["stage"], "pr")
        before = len(self.calls.read_text(encoding="utf-8").splitlines())

        second = self.run_loop(["opened"], PR="1")
        self.assertEqual(second.returncode, 0, second.stderr)
        after = self.calls.read_text(encoding="utf-8").splitlines()
        self.assertEqual(after[before:], ["opened"])

    def test_missing_outcome_keeps_stage_for_restart(self) -> None:
        failed = self.run_loop([])
        self.assertEqual(failed.returncode, 3)
        self.assertEqual(self.state()["stage"], "build")

        resumed = self.run_loop(
            ["complete", "approved", "production_ready", "opened"]
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)

    def test_rejected_rate_limit_stops_without_infrastructure_retries(self) -> None:
        result = self.run_loop(
            ["rate_limited"],
            timeout=3,
            INFRA_RETRIES="3",
            FAKE_RATE_LIMIT_SLEEP="10",
            **self.notify_env(),
        )

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(self.state()["stage"], "build")
        self.assertEqual(self.state()["attempts"]["build"], 0)
        self.assertEqual(
            self.calls.read_text(encoding="utf-8").splitlines(), ["rate_limited"]
        )
        self.assertIn("resetsAt=1787756400", result.stderr)
        self.assertEqual(
            self.notifications()[-1],
            ["PROJ-7", "rate_limited", "build rejected; resetsAt=1787756400"],
        )
        events = [
            json.loads(line)
            for line in (self.repo / "features" / "PROJ-7-example" / "loop.log")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        event = next(
            item for item in events if item.get("type") == "kaitersberg_rate_limit"
        )
        self.assertEqual(event["stage"], "build")
        self.assertEqual(event["resets_at"], 1787756400)

    def test_rejected_rate_limit_kills_term_resistant_descendants(self) -> None:
        child_pid_path = self.root / "rate-limit-child.pid"
        child_ready_path = self.root / "rate-limit-child.ready"
        child_pid: int | None = None
        try:
            result = self.run_loop(
                ["rate_limited"],
                timeout=4,
                FAKE_RATE_LIMIT_SLEEP="10",
                FAKE_RATE_LIMIT_CHILD_PID=str(child_pid_path),
                FAKE_RATE_LIMIT_CHILD_READY=str(child_ready_path),
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            deadline = time.monotonic() + 1
            while self.process_exists(child_pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertFalse(
                self.process_exists(child_pid),
                "TERM-resistant Claude descendant survived the rate-limit stop",
            )
        finally:
            if child_pid is not None and self.process_exists(child_pid):
                os.kill(child_pid, signal.SIGKILL)

    def test_review_permissions_are_scoped_to_the_resolved_feature(self) -> None:
        result = self.run_loop(["complete", "blocked"])
        self.assertEqual(result.returncode, 2, result.stderr)
        invocations = [
            json.loads(line)
            for line in self.claude_args.read_text(encoding="utf-8").splitlines()
        ]
        review_args = invocations[1]
        allowed = review_args[review_args.index("--allowedTools") + 1]
        self.assertIn(
            "Bash(mkdir -p features/PROJ-7-example/evidence/report-history)",
            allowed,
        )
        self.assertIn("Edit(features/PROJ-7-example/review.md)", allowed)
        self.assertIn(
            "Write(features/PROJ-7-example/evidence/report-history/*.md)", allowed
        )
        self.assertNotIn("features/**", allowed)

    def test_ci_failure_returns_through_build(self) -> None:
        result = self.run_loop(
            [
                "complete",
                "approved",
                "production_ready",
                "ci_failed",
                "complete",
                "approved",
                "production_ready",
                "opened",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["attempts"]["pr"], 1)

    def test_second_loop_is_locked_out(self) -> None:
        lock = self.repo / ".git" / "kaitersberg" / "loops" / "PROJ-7.lock"
        lock.mkdir(parents=True)
        result = self.run_loop(["complete"])
        self.assertEqual(result.returncode, 75)

    def test_hook_runs_after_transition_with_correlated_context(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready"],
            PR="0",
            **self.hook_env(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.hook_log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(
            [(call["STAGE"], call["persisted_stage"]) for call in calls],
            [("build", "review"), ("review", "qa"), ("qa", "pr")],
        )
        self.assertTrue(all(call["RUN_ID"] for call in calls))
        self.assertTrue(all(call["HEAD_SHA"] == "abc1234" for call in calls))
        self.assertTrue(all(call["NEXT_STAGE"] == call["persisted_stage"] for call in calls))

    def test_failing_hook_is_durable_and_does_not_change_loop_result(self) -> None:
        result = self.run_loop(["blocked"], **self.hook_env(HOOK_EXIT="23"))
        self.assertEqual(result.returncode, 2, result.stderr)
        events = [
            json.loads(line)
            for line in (self.repo / "features" / "PROJ-7-example" / "loop.log")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        receipt = next(event for event in events if event.get("type") == "kaitersberg_notification")
        self.assertEqual(receipt["exit_code"], 23)
        self.assertEqual(receipt["next_stage"], "build")
        self.assertIn("exit 23 (ignored)", result.stderr)

    def notify_env(self, **extra: str) -> dict[str, str]:
        return {
            "LOOP_NOTIFY": str(self.notifier),
            "NOTIFY_LOG": str(self.notify_log),
            **extra,
        }

    def notifications(self) -> list[list[str]]:
        return [
            line.split("\t")
            for line in self.notify_log.read_text(encoding="utf-8").splitlines()
        ]

    def test_notifier_receives_the_documented_events(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready", "opened"],
            **self.notify_env(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        events = self.notifications()
        self.assertEqual(len(events), 9)
        self.assertEqual(events[0], ["PROJ-7", "stage_started", "build round 1/3"])
        self.assertEqual(events[1], ["PROJ-7", "stage_done", "build round 1/3: complete"])
        self.assertEqual(events[-2], ["PROJ-7", "stage_done", "pr round 1/3: opened"])
        self.assertEqual(events[-1], ["PROJ-7", "finished", "PR opened"])
        self.assertEqual(self.state()["rounds"], 3)

    def test_pr_zero_notifies_finished_before_the_pull_request(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready"], PR="0", **self.notify_env()
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.notifications()[-1],
            ["PROJ-7", "finished", "stopped before PR (PR=0)"],
        )

    def test_blocked_stage_notifies_the_missing_decision(self) -> None:
        result = self.run_loop(["blocked"], **self.notify_env())
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(f"state: {self.state_path().resolve()}", result.stdout)
        self.assertIn(
            "events: "
            f"{(self.repo / 'features' / 'PROJ-7-example' / 'loop.log').resolve()}",
            result.stdout,
        )
        self.assertEqual(
            self.notifications()[-1],
            ["PROJ-7", "decision_needed", "which provider owns login"],
        )

    def test_exhausted_rounds_notify_the_stage_that_never_went_green(self) -> None:
        result = self.run_loop(
            ["complete", "changes_required"], ROUNDS="1", **self.notify_env()
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.notifications()[-1], ["PROJ-7", "rounds_exhausted", "review"])

    def test_failing_notifier_is_reported_and_never_breaks_the_loop(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready", "opened"],
            **self.notify_env(NOTIFY_EXIT="7"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["stage"], "complete")
        self.assertIn("LOOP_NOTIFY stage_started exited 7 (ignored)", result.stderr)

    def test_missing_notifier_never_breaks_the_loop(self) -> None:
        result = self.run_loop(
            ["complete", "approved", "production_ready", "opened"],
            LOOP_NOTIFY=str(self.root / "does-not-exist"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state()["stage"], "complete")

    def test_bug_2_hanging_notifier_is_bounded_without_timeout_binary(self) -> None:
        self.notifier.write_text(
            "#!/bin/sh\n"
            "trap 'exit 0' TERM\n"
            "python3 -c 'import os, pathlib, signal, time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "pathlib.Path(os.environ[\"NOTIFY_CHILD_READY\"]).write_text(\"ready\"); "
            "time.sleep(10)' &\n"
            "while [ ! -e \"$NOTIFY_CHILD_READY\" ]; do :; done\n"
            "wait\n",
            encoding="utf-8",
        )
        self.notifier.chmod(0o755)

        result = self.run_loop(
            ["blocked"],
            timeout=3,
            PATH=self.path_without_timeout(),
            LOOP_NOTIFY=str(self.notifier),
            LOOP_NOTIFY_TIMEOUT="0.1",
            LOOP_NOTIFY_KILL_GRACE="0.05",
            NOTIFY_CHILD_READY=str(self.root / "notify-child-ready"),
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("LOOP_NOTIFY stage_started exited 124 (ignored)", result.stderr)

    def test_retry_budget_cannot_be_bypassed_by_restart(self) -> None:
        first = self.run_loop(["complete", "changes_required"], ROUNDS="1")
        self.assertEqual(first.returncode, 1, first.stderr)
        before = self.calls.read_text(encoding="utf-8").splitlines()

        refused = self.run_loop(["complete"], ROUNDS="1")
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertEqual(self.calls.read_text(encoding="utf-8").splitlines(), before)

        resumed = self.run_loop(
            ["complete", "approved", "production_ready", "opened"], ROUNDS="2"
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)


if __name__ == "__main__":
    unittest.main()
