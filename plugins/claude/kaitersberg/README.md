# Kaitersberg plugin

This directory is the self-contained plugin installed by the Claude Code
marketplace.

- `skills/` is the generated Claude Code bundle.
- `.claude-plugin/plugin.json` defines the shared `kaitersberg`
  namespace.

Do not edit the skill tree here. Edit `.claude/skills/` at the repository root
and run `python3 scripts/port-to-codex.py`.
