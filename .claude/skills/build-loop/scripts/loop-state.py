#!/usr/bin/env python3
"""Persistent state and transition policy for loop-feature.sh."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


INITIAL = {
    "version": 1,
    "stage": "build",
    "last_outcome": None,
    "head_sha": None,
    "attempts": {"build": 0, "review": 0, "qa": 0, "pr": 0},
    "transitions": 0,
}

OUTCOMES = {
    "build": {"complete", "incomplete", "blocked"},
    "review": {
        "approved",
        "approved_with_notes",
        "changes_required",
        "incomplete",
        "blocked",
    },
    "qa": {
        "production_ready",
        "ready_with_reservations",
        "not_production_ready",
        "incomplete",
        "blocked",
    },
    "pr": {"opened", "ci_failed", "conflict", "incomplete", "blocked"},
}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def read_state(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or value.get("version") != 1:
        raise SystemExit(f"{path}: unsupported loop state")
    return value


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def initialise(
    path: Path, feature: str, run_id: str, stage: str, rounds: int | None = None
) -> dict[str, Any]:
    if path.exists():
        state = read_state(path)
        # The budget is per invocation; the persisted value is the operative one,
        # so a resume with a different ROUNDS records what it actually enforces.
        if rounds is not None and state.get("rounds") != rounds:
            state.update(rounds=rounds, updated_at=now())
            write_state(path, state)
        return state
    if stage not in OUTCOMES:
        raise SystemExit(f"invalid initial stage: {stage}")
    state = dict(INITIAL)
    state["attempts"] = dict(INITIAL["attempts"])
    state.update(
        feature=feature,
        run_id=run_id,
        stage=stage,
        rounds=rounds,
        created_at=now(),
        updated_at=now(),
    )
    write_state(path, state)
    return state


def transition(
    path: Path, stage: str, outcome: str, head_sha: str | None
) -> dict[str, Any]:
    state = read_state(path)
    current = state.get("stage")
    if current != stage:
        raise SystemExit(f"state is at {current}, not {stage}")
    if outcome not in OUTCOMES[stage]:
        raise SystemExit(f"invalid {stage} outcome: {outcome}")

    action = "continue"
    counter: str | None = None
    next_stage = stage

    if outcome == "blocked":
        action = "stop_blocked"
    elif outcome == "incomplete":
        counter = stage
    elif stage == "build":
        next_stage = "review"
    elif stage == "review":
        if outcome == "changes_required":
            counter = "review"
            next_stage = "build"
        else:
            next_stage = "qa"
    elif stage == "qa":
        if outcome == "not_production_ready":
            counter = "qa"
            next_stage = "build"
        else:
            next_stage = "pr"
    elif stage == "pr":
        if outcome in {"ci_failed", "conflict"}:
            counter = "pr"
            next_stage = "build"
        else:
            next_stage = "complete"
            action = "stop_ok"

    if counter:
        state["attempts"][counter] += 1
    state.update(
        stage=next_stage,
        last_stage=stage,
        last_outcome=outcome,
        head_sha=head_sha or state.get("head_sha"),
        transitions=int(state.get("transitions", 0)) + 1,
        updated_at=now(),
    )
    write_state(path, state)
    return {
        "action": action,
        "stage": next_stage,
        "counter": counter,
        "attempts": state["attempts"].get(counter, 0) if counter else 0,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("path", type=Path)
    init.add_argument("feature")
    init.add_argument("run_id")
    init.add_argument("--stage", choices=sorted(OUTCOMES), default="build")
    init.add_argument("--rounds", type=int)

    show = commands.add_parser("show")
    show.add_argument("path", type=Path)
    show.add_argument("--field")

    move = commands.add_parser("transition")
    move.add_argument("path", type=Path)
    move.add_argument("stage", choices=sorted(OUTCOMES))
    move.add_argument("outcome")
    move.add_argument("--head-sha")
    return result


def main() -> None:
    args = parser().parse_args()
    if args.command == "init":
        value: Any = initialise(
            args.path, args.feature, args.run_id, args.stage, args.rounds
        )
    elif args.command == "show":
        state = read_state(args.path)
        value = state.get(args.field) if args.field else state
    else:
        value = transition(args.path, args.stage, args.outcome, args.head_sha)

    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    elif value is not None:
        print(value)


if __name__ == "__main__":
    main()
