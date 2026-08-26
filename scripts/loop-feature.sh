#!/usr/bin/env bash
# Compatibility entry point for framework checkouts. Installed plugins use the
# runner bundled beside the build-loop skill instead.
set -euo pipefail

WRAPPER_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec "$WRAPPER_DIR/../.claude/skills/build-loop/scripts/loop-feature.sh" "$@"
