#!/usr/bin/env bash
# Start one bundled feature loop under tmux while keeping its complete output and
# final exit code below Git's common directory even when the tmux pane disappears.
set -euo pipefail

F=${1:-}
[[ $F =~ ^[A-Za-z]+-[0-9]+$ ]] || { echo "usage: $0 PROJ-x" >&2; exit 64; }
command -v tmux >/dev/null || { echo "tmux is required for a detached run" >&2; exit 69; }

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
RUNNER=$SCRIPT_DIR/loop-feature.sh
STATUS=$SCRIPT_DIR/loop-status.sh
[[ -x $RUNNER && -x $STATUS ]] \
  || { echo "missing executable build-loop runtime beside $0" >&2; exit 70; }

FEATURE_DIRS=(features/"$F"-*)
[[ ${#FEATURE_DIRS[@]} == 1 && -d ${FEATURE_DIRS[0]} ]] \
  || { echo "expected exactly one feature folder for $F" >&2; exit 66; }
D=${FEATURE_DIRS[0]}

GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null) \
  || { echo "run this inside a product repository" >&2; exit 64; }
[[ $GIT_COMMON == /* ]] || GIT_COMMON=$(pwd -P)/$GIT_COMMON
PRODUCT_ROOT=$(dirname "$GIT_COMMON")
STATE_DIR=$GIT_COMMON/kaitersberg/loops
STATE_FILE=$STATE_DIR/$F.json
EVENT_LOG=$PRODUCT_ROOT/$D/loop.log
SESSION=kaitersberg-$F

if tmux has-session -t "=$SESSION" 2>/dev/null; then
  echo "$F already has tmux session $SESSION" >&2
  exit 75
fi

mkdir -p "$STATE_DIR"
DETACHED_ID=$(date -u +%Y%m%dT%H%M%SZ)-$$
CAPTURE=$STATE_DIR/$F-$DETACHED_ID.detached.log
EXIT_FILE=$STATE_DIR/$F-$DETACHED_ID.detached.exit
EXIT_TMP=$EXIT_FILE.tmp

shell_quote() {
  local value=${1//\'/\'\\\'\'}
  printf "'%s'" "$value"
}

RUNNER_Q=$(shell_quote "$RUNNER")
FEATURE_Q=$(shell_quote "$F")
CAPTURE_Q=$(shell_quote "$CAPTURE")
EXIT_Q=$(shell_quote "$EXIT_FILE")
EXIT_TMP_Q=$(shell_quote "$EXIT_TMP")
COMMAND="umask 077; set +e; $RUNNER_Q $FEATURE_Q >$CAPTURE_Q 2>&1; code=\$?; printf '%s\\n' \"\$code\" >$EXIT_TMP_Q; mv $EXIT_TMP_Q $EXIT_Q; exit \"\$code\""

# A long-lived tmux server may have an older environment than this invocation.
# Pass only the runner controls and harness identity, never arbitrary repository
# variables. tmux receives each value as its own argv entry, not shell text.
TMUX_ENV=(-e "PATH=$PATH")
for name in \
  KAITERSBERG_HARNESS CODEX_THREAD_ID CODEX_SESSION_ID \
  CLAUDE_CODE_SESSION_ID CLAUDE_CODE_ENTRYPOINT CLAUDECODE \
  ROUNDS PR START_STAGE LOOP_RESET INFRA_RETRIES LOOP_NOTIFY \
  LOOP_NOTIFY_TIMEOUT LOOP_NOTIFY_KILL_GRACE STAGE_DONE_CMD MAX_TURNS \
  STAGE_TIMEOUT CODEX_SANDBOX SKILL_NS RUN_ID \
  CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS; do
  if printenv "$name" >/dev/null 2>&1; then
    TMUX_ENV+=(-e "$name=${!name}")
  fi
done

tmux new-session -d -s "$SESSION" -c "$PRODUCT_ROOT" \
  "${TMUX_ENV[@]}" "$COMMAND"

printf 'detached: accepted; current state unknown\n'
printf 'session: %s\n' "$SESSION"
printf 'state: %s\n' "$STATE_FILE"
printf 'events: %s\n' "$EVENT_LOG"
printf 'launcher log: %s\n' "$CAPTURE"
printf 'launcher exit: %s\n' "$EXIT_FILE"
# Not "attach and watch": the pane stays blank by construction, because the
# command above redirects the runner's entire output into the launcher log.
printf 'watch stage output: tail -n +1 -f %q\n' "$CAPTURE"
printf 'status: %q %q\n' "$STATUS" "$F"
printf 'follow: %q %q --follow\n' "$STATUS" "$F"
