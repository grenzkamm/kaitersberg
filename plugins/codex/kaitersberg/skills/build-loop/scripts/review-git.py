#!/usr/bin/env python3
"""Expose only read-only Git queries to an unattended review session."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


MAX_OUTPUT_BYTES = 1_000_000
def safe_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update(
        GIT_OPTIONAL_LOCKS="0",
        GIT_PAGER="cat",
        GIT_EXTERNAL_DIFF="",
        GIT_ATTR_NOSYSTEM="1",
    )
    return env


def safe_revision(value: str) -> str:
    if not value or value.startswith("-") or any(char in value for char in "\0\r\n"):
        raise argparse.ArgumentTypeError("revision must not be empty or start with '-'")
    return value


def run_git(repo: Path, arguments: list[str]) -> int:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-C",
            str(repo),
            *arguments,
        ],
        env=safe_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if len(result.stdout) > MAX_OUTPUT_BYTES:
        print(
            "review-git: output exceeds 1 MB; rerun the query for narrower paths",
            file=sys.stderr,
        )
        return 65
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    return result.returncode


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Read-only Git queries for Kaitersberg review sessions"
    )
    result.add_argument("--repo", type=Path, default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)

    commands.add_parser("status")
    commands.add_parser("worktree-list")
    commands.add_parser("branch-current")

    rev_parse = commands.add_parser("rev-parse")
    rev_parse.add_argument(
        "value", choices=("HEAD", "show-toplevel", "git-common-dir")
    )

    diff = commands.add_parser("diff")
    diff.add_argument("base", type=safe_revision)
    diff.add_argument("head", type=safe_revision)
    diff.add_argument("--mode", choices=("content", "stat", "names"), default="content")
    diff.add_argument("paths", nargs="*")

    show = commands.add_parser("show")
    show.add_argument("revision", type=safe_revision)
    show.add_argument("paths", nargs="*")

    log = commands.add_parser("log")
    log.add_argument("revision", type=safe_revision)
    log.add_argument("--max-count", type=int, default=100)
    log.add_argument("paths", nargs="*")

    merge_base = commands.add_parser("merge-base")
    merge_base.add_argument("left", type=safe_revision)
    merge_base.add_argument("right", type=safe_revision)

    ls_files = commands.add_parser("ls-files")
    ls_files.add_argument("paths", nargs="*")

    grep = commands.add_parser("grep")
    grep.add_argument("pattern")
    grep.add_argument("--revision", type=safe_revision)
    grep.add_argument("paths", nargs="*")
    return result


def command(args: argparse.Namespace) -> list[str]:
    if args.command == "status":
        return ["status", "--short", "--branch", "--untracked-files=all"]
    if args.command == "worktree-list":
        return ["worktree", "list", "--porcelain"]
    if args.command == "branch-current":
        return ["symbolic-ref", "--quiet", "--short", "HEAD"]
    if args.command == "rev-parse":
        value = {
            "HEAD": "HEAD",
            "show-toplevel": "--show-toplevel",
            "git-common-dir": "--git-common-dir",
        }[args.value]
        return ["rev-parse", value]
    if args.command == "diff":
        mode = {
            "content": [],
            "stat": ["--stat"],
            "names": ["--name-status"],
        }[args.mode]
        return [
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            *mode,
            f"{args.base}...{args.head}",
            "--",
            *args.paths,
        ]
    if args.command == "show":
        return [
            "show",
            "--no-ext-diff",
            "--no-textconv",
            "--format=fuller",
            args.revision,
            "--",
            *args.paths,
        ]
    if args.command == "log":
        if args.max_count < 1 or args.max_count > 1000:
            raise SystemExit("--max-count must be between 1 and 1000")
        return [
            "log",
            f"--max-count={args.max_count}",
            "--format=%H%x09%aI%x09%s",
            args.revision,
            "--",
            *args.paths,
        ]
    if args.command == "merge-base":
        return ["merge-base", args.left, args.right]
    if args.command == "ls-files":
        return ["ls-files", "--", *args.paths]
    result = ["grep", "-n", "--no-color", "-e", args.pattern]
    if args.revision:
        result.append(args.revision)
    return [*result, "--", *args.paths]


def main() -> int:
    args = parser().parse_args()
    return run_git(args.repo.resolve(), command(args))


if __name__ == "__main__":
    raise SystemExit(main())
