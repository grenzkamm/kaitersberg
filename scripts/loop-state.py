#!/usr/bin/env python3
"""Compatibility import and CLI for the state helper bundled with build-loop."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


TARGET = (
    Path(__file__).resolve().parents[1]
    / ".claude"
    / "skills"
    / "build-loop"
    / "scripts"
    / "loop-state.py"
)
SPEC = spec_from_file_location("kaitersberg_build_loop_state", TARGET)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load build-loop state helper from {TARGET}")
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

initialise = MODULE.initialise
read_state = MODULE.read_state
transition = MODULE.transition


if __name__ == "__main__":
    MODULE.main()
