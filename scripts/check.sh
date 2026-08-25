#!/usr/bin/env bash
#
# check.sh - everything this repository asks of a change, in one command.
#
#   scripts/check.sh            run every check
#   scripts/check.sh --staged   the same, but judge only what is staged (the hook)
#
# It is the pre-commit hook and it is what a person runs before pushing, so the
# two can never disagree about what "green" means.
#
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
FAILED=()
STAGED=${1:-}

step() {  # step <name> <command...>
  printf '\033[2m…\033[0m %s' "$1"
  local out
  if out=$("${@:2}" 2>&1); then
    printf '\r\033[32m✓\033[0m %s\n' "$1"
  else
    printf '\r\033[31m✗\033[0m %s\n' "$1"
    printf '%s\n' "$out" | sed 's/^/    /'
    FAILED+=("$1")
  fi
}

# The port is generated from .claude/skills, and a stale port is worse than none:
# it is a second version of the truth that nobody reads until it is wrong.
step "codex port and plugin bundles in step" python3 scripts/port-to-codex.py --check

# The rules this repository states about its own skills - handoffs, templates,
# frontmatter, English.
step "skills follow the repository's own rules" python3 scripts/lint-skills.py

# Em dashes had become a house style by accident and made the public prose harder
# to scan. Name the UTF-8 bytes instead of putting the character in this file, or
# the check would fail on itself.
EM_DASH=$(printf '\342\200\224')
no_em_dash() { ! git grep -Iq "$EM_DASH"; }
step "tracked text uses ASCII dashes" no_em_dash

for f in scripts/*.sh; do
  step "shellcheck ${f#scripts/}" shellcheck "$f"
done

for f in scripts/*.py; do
  if command -v ruff >/dev/null; then
    step "ruff ${f#scripts/}" ruff check --quiet "$f"
  else
    # No linter installed is not a reason to accept a file that will not parse.
    step "python parses ${f#scripts/}" python3 -m py_compile "$f"
  fi
done

step "loop transition behavior" python3 -m unittest discover -s tests

step "manifests are valid json and agree on the version" python3 - <<'PY'
import json, pathlib, sys
files = sorted(pathlib.Path(".").glob("**/*plugin*/*.json")) + [
    pathlib.Path(".claude-plugin/marketplace.json"), pathlib.Path(".agents/plugins/marketplace.json")]
versions = {}
for path in {p for p in files if p.is_file()}:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"{path}: {exc}")
    if isinstance(data, dict) and isinstance(data.get("version"), str):
        versions[str(path)] = data["version"]
bases = {v.split("+", 1)[0] for v in versions.values()}
if len(bases) > 1:
    sys.exit("plugin versions disagree: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
PY

# A cachebuster is for a local install, never for a commit: it would make every
# checkout claim a version that was only ever real on one machine.
if [[ $STAGED == --staged ]]; then
  step "no local cachebuster version staged" bash -c \
    '! git diff --cached -U0 -- "**/plugin.json" | grep -q "^+.*+codex\.local-"'
fi

if ((${#FAILED[@]})); then
  printf '\n\033[31m%d check(s) failed:\033[0m %s\n' "${#FAILED[@]}" "${FAILED[*]}"
  exit 1
fi
printf '\n\033[32mall checks passed\033[0m\n'
