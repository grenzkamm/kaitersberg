#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)
PLUGIN_NAME="kaitersberg"
MARKETPLACE_NAME="kaitersberg"
PLUGIN_SELECTOR="$PLUGIN_NAME@$MARKETPLACE_NAME"
CLAUDE_SCOPE="user"
DRY_RUN=0
BUMP_VERSION=1
CACHEBUSTER=""

usage() {
  cat <<'EOF'
Usage: scripts/update-installed-plugins.sh [options]

Refresh the locally installed Kaitersberg plugin for Codex and Claude
Code from this repository. By default, both plugin manifests receive the same
local cachebuster so neither host can reuse a stale cached version.

Options:
  --cachebuster TOKEN   Use TOKEN instead of a UTC timestamp.
  --no-version-bump     Install the version already present in both manifests.
  --claude-scope SCOPE  Claude install scope (default: user).
  --dry-run             Validate and print the planned actions without changing
                        manifests or plugin installations.
  -h, --help            Show this help.
EOF
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

print_command() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
}

run_mutating() {
  print_command "$@"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

check_marketplace_root() {
  local host=$1
  local configured_root=$2

  if [[ -z "$configured_root" ]]; then
    fail "$host marketplace $MARKETPLACE_NAME is not configured"
  fi
  if [[ "$configured_root" == "__NONLOCAL__" ]]; then
    fail "$host marketplace $MARKETPLACE_NAME is not a local directory source"
  fi

  local resolved_root
  resolved_root=$(CDPATH='' cd -- "$configured_root" 2>/dev/null && pwd -P) || \
    fail "$host marketplace directory does not exist: $configured_root"

  if [[ "$resolved_root" != "$REPO_ROOT" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      printf 'Warning: %s marketplace points to %s, not this worktree.\n' "$host" "$resolved_root" >&2
    else
      fail "$host marketplace points to $resolved_root, not $REPO_ROOT"
    fi
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cachebuster)
      [[ $# -ge 2 ]] || fail "--cachebuster requires a value"
      CACHEBUSTER=$2
      shift 2
      ;;
    --no-version-bump)
      BUMP_VERSION=0
      shift
      ;;
    --claude-scope)
      [[ $# -ge 2 ]] || fail "--claude-scope requires a value"
      CLAUDE_SCOPE=$2
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

case "$CLAUDE_SCOPE" in
  user|project|local|managed) ;;
  *) fail "invalid Claude scope: $CLAUDE_SCOPE" ;;
esac

require_command python3
require_command codex
require_command claude

CODEX_MANIFEST="$REPO_ROOT/plugins/codex/$PLUGIN_NAME/.codex-plugin/plugin.json"
CLAUDE_MANIFEST="$REPO_ROOT/plugins/claude/$PLUGIN_NAME/.claude-plugin/plugin.json"
CODEX_MARKETPLACE="$REPO_ROOT/.agents/plugins/marketplace.json"
CLAUDE_MARKETPLACE="$REPO_ROOT/.claude-plugin/marketplace.json"

[[ -f "$CODEX_MANIFEST" ]] || fail "missing Codex manifest: $CODEX_MANIFEST"
[[ -f "$CLAUDE_MANIFEST" ]] || fail "missing Claude manifest: $CLAUDE_MANIFEST"
[[ -f "$CODEX_MARKETPLACE" ]] || fail "missing Codex marketplace: $CODEX_MARKETPLACE"
[[ -f "$CLAUDE_MARKETPLACE" ]] || fail "missing Claude marketplace: $CLAUDE_MARKETPLACE"

codex_marketplace_root=$(
  codex plugin marketplace list | awk -v marketplace="$MARKETPLACE_NAME" '
    $1 == marketplace {
      $1 = ""
      sub(/^[[:space:]]+/, "")
      print
      exit
    }
  '
)
claude_marketplace_root=$(
  claude plugin marketplace list | awk -v marketplace="$MARKETPLACE_NAME" '
    found && /Source: Directory \(/ {
      line = $0
      sub(/^.*Source: Directory \(/, "", line)
      sub(/\).*$/, "", line)
      print line
      exit
    }
    found && /Source:/ { print "__NONLOCAL__"; exit }
    index($0, marketplace) { found = 1; next }
  '
)
check_marketplace_root "Codex" "$codex_marketplace_root"
check_marketplace_root "Claude" "$claude_marketplace_root"

manifest_data=$(
  python3 - "$CODEX_MANIFEST" "$CLAUDE_MANIFEST" "$CODEX_MARKETPLACE" "$CLAUDE_MARKETPLACE" <<'PY'
import json
import sys
from pathlib import Path

codex_manifest_path, claude_manifest_path, codex_marketplace_path, claude_marketplace_path = map(Path, sys.argv[1:])

def load(path):
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value

codex = load(codex_manifest_path)
claude = load(claude_manifest_path)
codex_marketplace = load(codex_marketplace_path)
claude_marketplace = load(claude_marketplace_path)

expected_name = "kaitersberg"
for path, payload in ((codex_manifest_path, codex), (claude_manifest_path, claude)):
    if payload.get("name") != expected_name:
        raise SystemExit(f"{path} must declare name {expected_name!r}")
    if not isinstance(payload.get("version"), str) or not payload["version"].strip():
        raise SystemExit(f"{path} must declare a non-empty string version")

for path, payload in ((codex_marketplace_path, codex_marketplace), (claude_marketplace_path, claude_marketplace)):
    if payload.get("name") != expected_name:
        raise SystemExit(f"{path} must declare marketplace name {expected_name!r}")
    entries = payload.get("plugins")
    if not isinstance(entries, list) or not any(entry.get("name") == expected_name for entry in entries if isinstance(entry, dict)):
        raise SystemExit(f"{path} has no plugin entry for {expected_name!r}")

codex_base = codex["version"].split("+", 1)[0]
claude_base = claude["version"].split("+", 1)[0]
if codex_base != claude_base:
    raise SystemExit(
        f"plugin base versions differ: Codex={codex['version']}, Claude={claude['version']}"
    )

print("\t".join((codex_base, codex["version"], claude["version"])))
PY
)

IFS=$'\t' read -r BASE_VERSION CODEX_SOURCE_VERSION CLAUDE_SOURCE_VERSION <<<"$manifest_data"

if [[ "$BUMP_VERSION" -eq 1 ]]; then
  if [[ -z "$CACHEBUSTER" ]]; then
    CACHEBUSTER="local-$(date -u +%Y%m%d-%H%M%S)"
  fi
  [[ "$CACHEBUSTER" =~ ^[a-z0-9][a-z0-9-]*$ ]] || \
    fail "cachebuster must use lowercase letters, digits and hyphens"
  TARGET_VERSION="$BASE_VERSION+codex.$CACHEBUSTER"
else
  [[ -z "$CACHEBUSTER" ]] || fail "--cachebuster cannot be combined with --no-version-bump"
  [[ "$CODEX_SOURCE_VERSION" == "$CLAUDE_SOURCE_VERSION" ]] || \
    fail "--no-version-bump requires identical Codex and Claude versions"
  TARGET_VERSION="$CODEX_SOURCE_VERSION"
fi

printf 'Repository: %s\n' "$REPO_ROOT"
printf 'Codex source version: %s\n' "$CODEX_SOURCE_VERSION"
printf 'Claude source version: %s\n' "$CLAUDE_SOURCE_VERSION"
printf 'Target version: %s\n' "$TARGET_VERSION"

python3 "$REPO_ROOT/scripts/port-to-codex.py" --check
claude plugin validate "$REPO_ROOT/plugins/claude/$PLUGIN_NAME"
claude plugin validate "$REPO_ROOT"

printf '\nCurrently installed:\n'
codex plugin list --json | python3 -c '
import json
import sys

selector = sys.argv[1]
payload = json.load(sys.stdin)
match = next((item for item in payload.get("installed", []) if item.get("pluginId") == selector), None)
print("  Codex: " + (match.get("version", "unknown") if match else "not installed"))
' "$PLUGIN_SELECTOR"

claude_version=$(
  claude plugin list | awk -v selector="$PLUGIN_SELECTOR" '
    index($0, selector) { found = 1; next }
    found && /Version:/ { print $2; exit }
  '
)
printf '  Claude: %s\n' "${claude_version:-not installed}"

if [[ "$BUMP_VERSION" -eq 1 ]]; then
  printf '\nUpdating both plugin manifests:\n'
  print_command python3 '<manifest updater>' "$TARGET_VERSION"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    python3 - "$TARGET_VERSION" "$CODEX_MANIFEST" "$CLAUDE_MANIFEST" <<'PY'
import json
import os
import sys
from pathlib import Path

version = sys.argv[1]
paths = [Path(value) for value in sys.argv[2:]]
payloads = []

for path in paths:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["version"] = version
    payloads.append((path, payload))

for path, payload in payloads:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
PY
  fi
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  claude plugin validate "$REPO_ROOT/plugins/claude/$PLUGIN_NAME"
  claude plugin validate "$REPO_ROOT"
fi

printf '\nRefreshing Codex:\n'
run_mutating codex plugin add "$PLUGIN_SELECTOR" --json

printf '\nRefreshing Claude Code:\n'
run_mutating claude plugin marketplace update "$MARKETPLACE_NAME"
run_mutating claude plugin update "$PLUGIN_SELECTOR" --scope "$CLAUDE_SCOPE" --yes

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '\nDry run complete; no manifests or installations were changed.\n'
  exit 0
fi

printf '\nInstalled after update:\n'
codex plugin list --json | python3 -c '
import json
import sys

selector, expected = sys.argv[1:]
payload = json.load(sys.stdin)
match = next((item for item in payload.get("installed", []) if item.get("pluginId") == selector), None)
if not match:
    raise SystemExit(f"Codex plugin is not installed: {selector}")
actual = match.get("version")
if actual != expected:
    raise SystemExit(f"Codex installed version mismatch: expected {expected}, got {actual}")
print(f"  Codex: {actual}")
' "$PLUGIN_SELECTOR" "$TARGET_VERSION"

claude_version=$(
  claude plugin list | awk -v selector="$PLUGIN_SELECTOR" '
    index($0, selector) { found = 1; next }
    found && /Version:/ { print $2; exit }
  '
)
[[ "$claude_version" == "$TARGET_VERSION" ]] || \
  fail "Claude installed version mismatch: expected $TARGET_VERSION, got ${claude_version:-not installed}"
printf '  Claude: %s\n' "$claude_version"

printf '\nUpdate complete. Start a new Codex thread and restart Claude Code before testing the updated skills.\n'
