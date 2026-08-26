#!/usr/bin/env python3
"""Compatibility CLI for the Git helper bundled with build-loop."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TARGET = (
    Path(__file__).resolve().parents[1]
    / ".claude"
    / "skills"
    / "build-loop"
    / "scripts"
    / "review-git.py"
)
SPEC = spec_from_file_location("kaitersberg_build_loop_review_git", TARGET)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load build-loop Git helper from {TARGET}")
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


if __name__ == "__main__":
    raise SystemExit(MODULE.main())
