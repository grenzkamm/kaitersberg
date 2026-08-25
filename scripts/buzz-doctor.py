#!/usr/bin/env python3
"""Diagnose the Kaitersberg-to-Buzz delivery path from a product repository.

The default mode is read-only. --probe-webhook is deliberately active: it sends
one webhook request, which should create a workflow message and wake the Builder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


FEATURE_ID = re.compile(r"^[A-Za-z]+-[0-9]+$")
SECRET = re.compile(r"(?i)(X-Webhook-Secret\s*[:=]\s*)\S+")
NSEC = re.compile(r"\bnsec1[023456789acdefghjklmnpqrstuvwxyz]+\b", re.IGNORECASE)


@dataclass
class Check:
    section: str
    name: str
    status: str
    detail: str
    fix: str = ""
    code: str = ""


def redacted(value: str) -> str:
    return NSEC.sub("<redacted-nsec>", SECRET.sub(r"\1<redacted>", value.strip()))


def command(*args: str, cwd: Path | None = None, timeout: int = 10) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, redacted(result.stdout), redacted(result.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", redacted(str(exc))


def git_path(root: Path, *parts: str) -> Path | None:
    code, output, _ = command("git", "rev-parse", "--git-common-dir", cwd=root)
    if code:
        return None
    common = Path(output)
    if not common.is_absolute():
        common = root / common
    return common.resolve().joinpath(*parts)


def read_json(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def log_facts(path: Path) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-600:]
    except OSError:
        return facts
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "kaitersberg_stage":
            facts["stage"] = event.get("stage")
            facts["run_id"] = event.get("run_id")
        elif kind == "result":
            facts["outcome"] = (event.get("structured_output") or {}).get("outcome")
        elif kind == "kaitersberg_transition":
            facts["transition"] = event
            facts["stage"] = event.get("next_stage")
            facts["run_id"] = event.get("run_id")
        elif kind == "kaitersberg_notification":
            facts["notification"] = event
    facts["age_seconds"] = max(0, int(time.time() - path.stat().st_mtime))
    return facts


def process_for(feature: str) -> tuple[str, str]:
    code, output, _ = command("ps", "-axo", "pid=,etime=,command=")
    if code:
        return "", ""
    for line in output.splitlines():
        if "loop-feature.sh" in line and re.search(rf"\b{re.escape(feature)}\b", line):
            fields = line.strip().split(None, 2)
            if len(fields) == 3:
                return fields[0], fields[1]
    return "", ""


def buzz_check(args: argparse.Namespace, checks: list[Check]) -> None:
    if not (args.channel or args.workflow or args.builder):
        return
    if not shutil.which("buzz"):
        checks.append(Check("Buzz", "CLI", "fail", "buzz is not on PATH", code="buzz_missing"))
        return

    def inspect(name: str, *call: str) -> str:
        code, output, error = command("buzz", "--format", "json", *call)
        if code:
            detail = error or output or f"exit {code}"
            checks.append(Check("Buzz", name, "fail", detail, code=f"buzz_{name}_failed"))
            return ""
        checks.append(Check("Buzz", name, "ok", "reachable and readable"))
        return output

    members = ""
    workflow = ""
    if args.channel:
        inspect("channel", "channels", "get", "--channel", args.channel)
        members = inspect("members", "channels", "members", "--channel", args.channel)
        inspect("canvas", "canvas", "get", "--channel", args.channel)
    if args.workflow:
        workflow = inspect("workflow", "workflows", "get", "--workflow", args.workflow)
        inspect("workflow runs", "workflows", "runs", "--workflow", args.workflow, "--limit", "5")
    if args.builder and members:
        if args.builder.casefold() in members.casefold():
            checks.append(Check("Buzz", "Builder membership", "ok", args.builder))
        else:
            checks.append(Check(
                "Buzz", "Builder membership", "fail", f"{args.builder} is not in the channel output",
                code="builder_not_member",
            ))
    if args.builder and workflow:
        mention = f"@{args.builder}"
        if mention.casefold() in workflow.casefold():
            checks.append(Check("Buzz", "Builder mention", "ok", mention))
        else:
            checks.append(Check(
                "Buzz", "Builder mention", "warn", f"{mention} was not found in the workflow",
                code="builder_not_mentioned",
            ))


def probe_webhook(url: str, secret_env: str) -> Check:
    secret = os.environ.get(secret_env, "")
    if not secret:
        return Check(
            "Buzz", "webhook probe", "fail", f"{secret_env} is not set",
            fix=f"export {secret_env}=<workflow secret>", code="probe_secret_missing",
        )
    request = urllib.request.Request(
        url,
        data=b"",
        method="POST",
        headers={"X-Webhook-Secret": secret, "User-Agent": "kaitersberg-buzz-doctor/1"},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        return Check(
            "Buzz", "webhook probe", "fail", f"HTTP {exc.code}",
            code="probe_http_error",
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        return Check(
            "Buzz", "webhook probe", "fail", redacted(str(exc.reason if hasattr(exc, "reason") else exc)),
            code="probe_network_error",
        )
    elapsed = int((time.monotonic() - started) * 1000)
    status_name = "ok" if status == 202 else "warn"
    return Check(
        "Buzz", "webhook probe", status_name, f"HTTP {status} in {elapsed} ms; a visible workflow message was requested",
        code="" if status == 202 else "probe_unexpected_status",
    )


def collect(args: argparse.Namespace) -> tuple[list[Check], dict[str, Any]]:
    checks: list[Check] = []
    context: dict[str, Any] = {"feature": args.feature, "generated_at": datetime.now(UTC).isoformat(timespec="seconds")}
    code, root_value, error = command("git", "rev-parse", "--show-toplevel")
    if code:
        checks.append(Check("Local", "product repository", "fail", error or "not inside a git repository", code="not_git"))
        return checks, context
    root = Path(root_value)
    context["root"] = str(root)
    checks.append(Check("Local", "product repository", "ok", str(root)))

    board = root / "features" / "INDEX.md"
    checks.append(Check(
        "Local", "feature board", "ok" if board.is_file() else "fail",
        str(board) if board.is_file() else "features/INDEX.md is missing", code="" if board.is_file() else "board_missing",
    ))
    for tool in ("buzz", "claude", "tmux", "jq"):
        location = shutil.which(tool)
        checks.append(Check("Local", tool, "ok" if location else "warn", location or "not on PATH", code="" if location else f"{tool}_missing"))
    if shutil.which("claude"):
        plugin_code, plugins, plugin_error = command("claude", "plugin", "list", "--json")
        installed = plugin_code == 0 and "kaitersberg" in plugins.casefold()
        checks.append(Check(
            "Local", "kaitersberg plugin", "ok" if installed else "warn",
            "installed" if installed else (plugin_error or "not found in claude plugin list"),
            code="" if installed else "plugin_missing",
        ))

    if not args.feature:
        buzz_check(args, checks)
        if args.probe_webhook:
            checks.append(probe_webhook(args.probe_webhook, args.secret_env))
        return checks, context

    feature = args.feature.upper()
    context["feature"] = feature
    matches = sorted((root / "features").glob(f"{feature}-*"))
    if len(matches) != 1:
        checks.append(Check(
            "Loop", "feature folder", "fail", f"expected one features/{feature}-* folder, found {len(matches)}",
            code="feature_folder",
        ))
        buzz_check(args, checks)
        return checks, context
    feature_dir = matches[0]
    checks.append(Check("Loop", "feature folder", "ok", str(feature_dir.relative_to(root))))

    state_path = git_path(root, "kaitersberg", "loops", f"{feature}.json")
    lock_path = git_path(root, "kaitersberg", "loops", f"{feature}.lock")
    state = read_json(state_path)
    context["state"] = {
        key: state.get(key)
        for key in ("version", "stage", "last_outcome", "head_sha", "attempts", "transitions", "updated_at")
        if key in state
    }
    if state:
        attempts = ", ".join(f"{key} {value}" for key, value in state.get("attempts", {}).items() if value) or "no retries"
        checks.append(Check("Loop", "persisted state", "ok", f"{state.get('stage', '?')} · {attempts}"))
    else:
        checks.append(Check("Loop", "persisted state", "warn", "no loop state yet", code="state_missing"))

    pid, elapsed = process_for(feature)
    context["pid"] = pid or None
    if pid:
        checks.append(Check("Loop", "process", "ok", f"pid {pid}, elapsed {elapsed}"))
    elif state and state.get("stage") != "complete":
        checks.append(Check(
            "Loop", "process", "warn", f"no running loop; persisted stage is {state.get('stage')}",
            fix=f"restart scripts/loop-feature.sh {feature}", code="loop_stopped",
        ))
    else:
        checks.append(Check("Loop", "process", "ok", "not running"))

    locked = bool(lock_path and lock_path.is_dir())
    if locked and not pid:
        checks.append(Check(
            "Loop", "lock", "fail", f"stale lock: {lock_path}",
            fix=f"verify no loop process exists, then rmdir {lock_path}", code="stale_lock",
        ))
    else:
        checks.append(Check("Loop", "lock", "ok", "held by the live loop" if locked else "not held"))

    code, _, _ = command("tmux", "has-session", "-t", feature)
    checks.append(Check(
        "Loop", "tmux session", "ok" if code == 0 else ("warn" if pid else "ok"),
        feature if code == 0 else ("loop runs outside the expected session" if pid else "not running"),
        code="" if code == 0 or not pid else "tmux_session_missing",
    ))

    log = feature_dir / "loop.log"
    facts = log_facts(log) if log.is_file() else {}
    context["log"] = {
        key: facts.get(key)
        for key in ("stage", "run_id", "outcome", "age_seconds")
        if key in facts
    }
    if facts.get("notification"):
        receipt = facts["notification"]
        context["log"]["notification"] = {
            key: receipt.get(key)
            for key in ("run_id", "stage", "outcome", "next_stage", "exit_code", "duration_seconds", "at")
            if key in receipt
        }
    if facts:
        age = facts.get("age_seconds", 0)
        status = "warn" if pid and age > 120 else "ok"
        checks.append(Check(
            "Loop", "last activity", status, f"{age}s ago · {facts.get('stage', '?')}",
            fix=f"tail -f {log}" if status == "warn" else "", code="loop_stalled" if status == "warn" else "",
        ))
    else:
        checks.append(Check("Loop", "event log", "warn", "loop.log has no readable events", code="log_missing"))

    notification = facts.get("notification") or {}
    if notification:
        exit_code = int(notification.get("exit_code", 1))
        checks.append(Check(
            "Buzz bridge", "last notification", "ok" if exit_code == 0 else "fail",
            f"{notification.get('stage', '?')} → {notification.get('next_stage', '?')} · exit {exit_code} · {notification.get('at', '?')}",
            fix="run the active webhook probe with --probe-webhook" if exit_code else "",
            code="" if exit_code == 0 else "notification_failed",
        ))
    else:
        checks.append(Check(
            "Buzz bridge", "notification receipt", "warn", "none recorded; the loop may predate hook telemetry or have no hook",
            code="notification_missing",
        ))

    buzz_check(args, checks)
    if args.probe_webhook:
        checks.append(probe_webhook(args.probe_webhook, args.secret_env))
    return checks, context


def diagnosis(checks: list[Check], feature: str | None) -> tuple[str, str]:
    priority = [
        "stale_lock", "notification_failed", "loop_stalled", "loop_stopped",
        "builder_not_member", "builder_not_mentioned", "probe_http_error",
        "probe_network_error", "board_missing", "not_git",
    ]
    by_code = {check.code: check for check in checks if check.code}
    for code in priority:
        if code not in by_code:
            continue
        check = by_code[code]
        messages = {
            "stale_lock": "The loop is gone but its lock remains.",
            "notification_failed": "The delivery loop advanced, but its Buzz notification hook failed.",
            "loop_stalled": "The loop process exists, but its event log stopped moving.",
            "loop_stopped": "The feature has resumable state, but no delivery loop is running.",
            "builder_not_member": "The configured Builder is not visible in the product channel.",
            "builder_not_mentioned": "The workflow does not appear to mention the configured Builder.",
            "probe_http_error": "The Buzz webhook rejected the active probe.",
            "probe_network_error": "The Buzz webhook could not be reached.",
            "board_missing": "This repository has no Kaitersberg feature board.",
            "not_git": "Run the doctor from a product repository.",
        }
        return messages[code], check.fix
    failures = [check for check in checks if check.status == "fail"]
    if failures:
        return failures[0].detail, failures[0].fix
    warnings = [check for check in checks if check.status == "warn"]
    if warnings:
        return "No hard failure was found; the warnings above are the remaining blind spots.", warnings[0].fix
    suffix = f" for {feature}" if feature else ""
    return f"All inspected layers are healthy{suffix}.", ""


def render(checks: list[Check], context: dict[str, Any], as_json: bool) -> int:
    summary, next_step = diagnosis(checks, context.get("feature"))
    if as_json:
        print(json.dumps({
            "schema_version": 1,
            "read_only": not context.get("probe_webhook", False),
            "context": context,
            "checks": [asdict(check) for check in checks],
            "diagnosis": summary,
            "next": next_step or None,
        }, ensure_ascii=False, indent=2))
    else:
        title = "Kaitersberg over Buzz"
        if context.get("feature"):
            title += f" · {context['feature']}"
        print(title)
        current = ""
        icons = {"ok": "✓", "warn": "!", "fail": "✗"}
        for check in checks:
            if check.section != current:
                current = check.section
                print(f"\n{current}")
            print(f"  {icons[check.status]} {check.name:<22} {check.detail}")
        print(f"\nDiagnosis\n  {summary}")
        if next_step:
            print(f"\nNext\n  {next_step}")
    if any(check.status == "fail" for check in checks):
        return 2
    if any(check.status == "warn" for check in checks):
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("feature", nargs="?", type=str.upper)
    result.add_argument("--channel", default=os.environ.get("BUZZ_CHANNEL_ID", ""), help="Buzz channel UUID")
    result.add_argument("--workflow", default=os.environ.get("BUZZ_WORKFLOW_ID", ""), help="Buzz workflow UUID")
    result.add_argument("--builder", default=os.environ.get("BUZZ_BUILDER", ""), help="Builder display name")
    result.add_argument("--probe-webhook", metavar="URL", help="actively POST one webhook request")
    result.add_argument("--secret-env", default="BUZZ_WEBHOOK_SECRET", help="environment variable holding the webhook secret")
    result.add_argument("--follow", action="store_true", help="refresh the terminal until interrupted")
    result.add_argument("--interval", type=float, default=5.0, help="follow refresh interval in seconds")
    result.add_argument("--json", action="store_true", help="emit a versioned JSON report")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.feature and not FEATURE_ID.fullmatch(args.feature):
        parser().error("feature must look like PROJ-3")
    if args.follow and args.json:
        parser().error("--follow and --json cannot be combined")
    if args.follow and args.probe_webhook:
        parser().error("--follow cannot repeat an active webhook probe")
    try:
        while True:
            checks, context = collect(args)
            context["probe_webhook"] = bool(args.probe_webhook)
            if args.follow:
                print("\033[2J\033[H", end="")
            exit_code = render(checks, context, args.json)
            if not args.follow:
                return exit_code
            time.sleep(max(0.5, args.interval))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
