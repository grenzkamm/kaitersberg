#!/usr/bin/env bash
#
# loop-feature.sh PROJ-x
#
# Drives one feature through /build -> /review -> /qa without a person in the
# chair, and stops where the framework wants one. Run it in the *product*
# repository, not here, with the kaitersberg plugin installed.
#
# Every stage is its own `claude -p` or `codex exec` process. That is the
# load-bearing part:
# a new process is a new session, so /review gets the fresh session it requires
# instead of merely asking for one.
#
# A green run opens the pull request. /pr has to be confirmed before it pushes,
# and starting the loop is that confirmation, given once for the run - the rule is
# satisfied, not bypassed. Start it with PR=0 to stop before that step instead.
# /merge is never automated: a merge is the irreversible one, and a person makes it.
#
# Watching it: the tool calls of the running stage go to stderr as they happen.
# The raw event stream is appended to <feature>/loop.log, so a second terminal
# can read what a Claude stage says as it says it with
#   tail -n +1 -f features/PROJ-x-*/loop.log | jq -Rr --unbuffered 'fromjson?
#     | select(.type=="assistant") | .message.content[]?
#     | select(.type=="text") | .text + "\n---"'
# (a codex stage emits other event shapes - adjust the filter); the bundled
# loop-status.sh --follow prints only the loop's own kaitersberg events.
#
# Outliving the window: every stage is a child of the shell that started this, so
# closing the terminal - or ending the agent session that started it for you - kills
# the stage in flight with its work uncommitted. Use build-loop's detached mode;
# it resolves this installed path and returns the session and observation commands.
#
# Being told what happens: set LOOP_NOTIFY to an executable and the loop runs it
# as  <notifier> <feature> <event> <detail>  at its decision points -
# stage_started and stage_done with "stage round X/Y", decision_needed with the
# reason the plan is silent, rounds_exhausted with the stage that never went
# green, rate_limited with Claude's resetsAt, and finished with "PR opened" or
# "stopped before PR (PR=0)". The loop
# knows no vendor: scripts/notify-ntfy.sh is a worked example, and wrapping the
# whole run still works too:
#   ntfy done -- scripts/loop-feature.sh PROJ-3
# A failing, missing or hanging notifier is reported and ignored - notification
# is never load-bearing. The bundled loop-status.sh reads the state this script
# persists without touching it.
# Being told per stage: set STAGE_DONE_CMD to a shell command; it runs after every
# stage outcome and its persisted transition with STAGE, OUTCOME, FEATURE, RUN_ID,
# HEAD_SHA, NEXT_STAGE and ACTION in its environment. A failing hook is recorded,
# reported and ignored - notification is never load-bearing.
#   STAGE_DONE_CMD='curl --fail-with-body -sS -o /dev/null -X POST https://relay/hooks/<id> -H "X-Webhook-Secret: <s>"' \
#     scripts/loop-feature.sh PROJ-3
# Exit codes: 0 green, 1 no green result, 2 a decision is needed, 3 a run failed.
# Spend is not capped here: the runs go through the subscription. Claude's
# MAX_TURNS stops a stage that circles; both harnesses have STAGE_TIMEOUT as the
# wall-clock bound. Reaching Claude's turn limit is not a failure: the stage goes
# round again.
#
#   PR=0 scripts/loop-feature.sh PROJ-3   # ... and stop before the pull request
#
set -euo pipefail

F=${1:-}
[[ $F =~ ^[A-Za-z]+-[0-9]+$ ]] || { echo "usage: $0 PROJ-x" >&2; exit 64; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 69; }

resolve_harness() {
  local requested=${KAITERSBERG_HARNESS:-auto}
  case $requested in
    claude|codex) printf '%s\n' "$requested" ;;
    auto)
      if [[ -n ${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-} ]] && command -v codex >/dev/null; then
        printf '%s\n' codex
      elif [[ -n ${CLAUDE_CODE_SESSION_ID:-}${CLAUDE_CODE_ENTRYPOINT:-}${CLAUDECODE:-} ]] \
        && command -v claude >/dev/null; then
        printf '%s\n' claude
      elif command -v claude >/dev/null && ! command -v codex >/dev/null; then
        printf '%s\n' claude
      elif command -v codex >/dev/null && ! command -v claude >/dev/null; then
        printf '%s\n' codex
      elif command -v claude >/dev/null && command -v codex >/dev/null; then
        echo "both claude and codex are installed; set KAITERSBERG_HARNESS=claude or codex" >&2
        return 64
      else
        echo "neither claude nor codex is installed" >&2
        return 69
      fi
      ;;
    *)
      echo "invalid KAITERSBERG_HARNESS=$requested (expected auto, claude or codex)" >&2
      return 64
      ;;
  esac
}

HARNESS=$(resolve_harness) || exit $?
command -v "$HARNESS" >/dev/null || { echo "$HARNESS is required" >&2; exit 69; }

# macOS ships no `timeout`; coreutils installs it as `gtimeout`. Claude stages use
# the Python supervisor below and remain wall-clock bounded without either command.
# A Codex stage runs uncapped rather than not at all - its harness still bounds a
# turn, it just takes longer to say so.
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || echo "")
[[ -n $TIMEOUT_BIN ]] || echo "note: no timeout(1) found, Codex stages run without a wall clock" >&2

FEATURE_DIRS=(features/"$F"-*)
[[ ${#FEATURE_DIRS[@]} == 1 && -d ${FEATURE_DIRS[0]} ]] || {
  echo "expected exactly one feature folder for $F" >&2; exit 66;
}
D=${FEATURE_DIRS[0]}

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
STATE_HELPER=$SCRIPT_DIR/loop-state.py
[[ -f $STATE_HELPER ]] || { echo "missing loop state helper: $STATE_HELPER" >&2; exit 70; }
REVIEW_GIT_HELPER=$SCRIPT_DIR/review-git.py
[[ -x $REVIEW_GIT_HELPER ]] || { echo "missing executable review git helper: $REVIEW_GIT_HELPER" >&2; exit 70; }

GIT_COMMON=$(git rev-parse --git-common-dir)
[[ $GIT_COMMON == /* ]] || GIT_COMMON=$(pwd)/$GIT_COMMON
STATE_DIR=$GIT_COMMON/kaitersberg/loops
STATE_FILE=$STATE_DIR/$F.json
LOCK_DIR=$STATE_DIR/$F.lock
PID_FILE=$STATE_DIR/$F.pid
mkdir -p "$STATE_DIR"
mkdir "$LOCK_DIR" 2>/dev/null || {
  echo "$F already has a loop lock at $LOCK_DIR" >&2; exit 75;
}
RUN_TMP=$(mktemp -d)
trap 'rm -rf -- "$RUN_TMP"; rm -f -- "$PID_FILE"; rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT
printf '%s\n' "$$" > "$PID_FILE"

if [[ ${LOOP_RESET:-0} == 1 && -f $STATE_FILE ]]; then
  mv "$STATE_FILE" "$STATE_FILE.$(date -u +%Y%m%dT%H%M%SZ).bak"
fi

RUN_ID=${RUN_ID:-"$(date -u +%Y%m%dT%H%M%SZ)-$$"}
START_STAGE=${START_STAGE:-build}
ROUNDS=${ROUNDS:-3}  # maximum persisted red/incomplete outcomes per stage
# The budget is persisted so the bundled read-only loop-status.sh can
# show "round X/Y" and tell an exhausted loop from a merely stopped one.
python3 "$STATE_HELPER" init "$STATE_FILE" "$F" "$RUN_ID" \
  --stage "$START_STAGE" --rounds "$ROUNDS" >/dev/null
RUN_ID=$(python3 "$STATE_HELPER" show "$STATE_FILE" --field run_id)
printf '%s: state: %s\n' "$F" "$STATE_FILE"
printf '%s: events: %s/%s/loop.log\n' "$F" "$(pwd -P)" "$D"

# /build dispatches its tasks as background subagents, and `claude -p` kills those
# ten minutes after its own turn ends - which is how the first PROJ-3 run lost an
# unfinished task with its work uncommitted. 0 means wait for them.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS:-0}

PR=${PR:-1}          # open the pull request after QA allows delivery; PR=0 stops before it
SKILL_NS=${SKILL_NS:-kaitersberg}
INFRA_RETRIES=${INFRA_RETRIES:-3}
STAGE_DONE_CMD=${STAGE_DONE_CMD:-}  # per-stage notification hook, see header
LOOP_NOTIFY=${LOOP_NOTIFY:-}        # per-event notifier executable, see header
LOOP_NOTIFY_TIMEOUT=${LOOP_NOTIFY_TIMEOUT:-30}  # seconds per notification
LOOP_NOTIFY_KILL_GRACE=${LOOP_NOTIFY_KILL_GRACE:-1}  # seconds between TERM and KILL

notify() { # notify <event> <detail> - never load-bearing: a failing, missing or
  # hanging notifier is reported and ignored, so it can never stop the loop.
  [[ -n $LOOP_NOTIFY ]] || return 0
  local code=0
  # Python is already required by the persisted-state helper. Use it here too so
  # notifier isolation does not silently disappear on macOS without coreutils.
  python3 - "$LOOP_NOTIFY_TIMEOUT" "$LOOP_NOTIFY_KILL_GRACE" \
    "$LOOP_NOTIFY" "$F" "$1" "$2" <<'PY' || code=$?
import errno
import os
import signal
import subprocess
import sys
import time

try:
    seconds = float(sys.argv[1])
    if seconds <= 0:
        raise ValueError
except ValueError:
    print("LOOP_NOTIFY_TIMEOUT must be a positive number", file=sys.stderr)
    raise SystemExit(64)

try:
    kill_grace = float(sys.argv[2])
    if kill_grace <= 0:
        raise ValueError
except ValueError:
    print("LOOP_NOTIFY_KILL_GRACE must be a positive number", file=sys.stderr)
    raise SystemExit(64)

try:
    process = subprocess.Popen(sys.argv[3:], start_new_session=True)
except OSError as error:
    print(error, file=sys.stderr)
    raise SystemExit(127 if error.errno == errno.ENOENT else 126)

try:
    returncode = process.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    deadline = time.monotonic() + kill_grace
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.05, remaining))

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        # Darwin may report EPERM for an orphaned group after delivering the
        # signal to its remaining member. The inherited pipes still prove below
        # whether any notifier descendant survived.
        pass
    process.wait()
    raise SystemExit(124)

raise SystemExit(returncode if returncode >= 0 else 128 - returncode)
PY
  (( code == 0 )) || echo "$F: LOOP_NOTIFY $1 exited $code (ignored)" >&2
}

# Writing stages may edit and run things; reading stages may not. `dontAsk` turns
# the "/review and /qa fix nothing" rule into something the harness enforces
# rather than something the model is asked to remember. It also denies
# AskUserQuestion, so a stage that needs a decision ends the run instead of
# guessing at one.
WRITE=(--permission-mode acceptEdits --allowedTools "Bash,Read,Edit,Write,Glob,Grep,Agent,Skill")
# Review may replace only its own report. Raw git is not read-only: checkout, clean,
# apply and shell aliases all fit Bash(git *). The helper exposes fixed query shapes,
# disables external diff commands and receives no arbitrary git options. Review's
# parallel lanes get Agent and inherit the same limits.
READ=(--permission-mode dontAsk --allowedTools "Read,Glob,Grep,Bash($REVIEW_GIT_HELPER *),Bash(mkdir -p $D/evidence/report-history),Agent,Edit($D/review.md),Write($D/evidence/report-history/*.md)")

claude_run() {
  # Claude reports rejected capacity in-band and may then leave the process alive.
  # Supervise it as its own process group so that event can stop the whole stage
  # immediately. Python is already a dependency of the persisted-state helper.
  python3 - "${STAGE_TIMEOUT:-3h}" "$@" <<'PY'
import json
import os
import re
import selectors
import signal
import subprocess
import sys
import time


def seconds(value: str) -> float:
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([smhd]?)", value)
    if not match:
        print(f"invalid STAGE_TIMEOUT={value}", file=sys.stderr)
        raise SystemExit(64)
    scale = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
    return float(match.group(1)) * scale


def stop_group(process: subprocess.Popen[bytes]) -> None:
    pgid = process.pid
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            pass
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.05, remaining))

    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    process.wait()


limit = seconds(sys.argv[1])
process = subprocess.Popen(
    ["claude", *sys.argv[2:]],
    stdout=subprocess.PIPE,
    start_new_session=True,
)


def interrupted(signum: int, _frame: object) -> None:
    stop_group(process)
    raise SystemExit(128 + signum)


signal.signal(signal.SIGINT, interrupted)
signal.signal(signal.SIGTERM, interrupted)
assert process.stdout is not None
selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)
deadline = time.monotonic() + limit
pending = b""
rejected = False

while selector.get_map():
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        stop_group(process)
        print(f"Claude stage exceeded STAGE_TIMEOUT={sys.argv[1]}", file=sys.stderr)
        raise SystemExit(124)
    events = selector.select(min(remaining, 0.25))
    if not events and process.poll() is not None:
        events = [(selector.get_key(process.stdout), selectors.EVENT_READ)]
    for key, _ in events:
        chunk = os.read(key.fileobj.fileno(), 65536)
        if not chunk:
            selector.unregister(key.fileobj)
            continue
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        pending += chunk
        lines = pending.split(b"\n")
        pending = lines.pop()
        for raw in lines:
            try:
                event = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            info = event.get("rate_limit_info") or {}
            if event.get("type") == "rate_limit_event" and info.get("status") == "rejected":
                rejected = True
                stop_group(process)
                break
        if rejected:
            break
    if rejected:
        break

if rejected:
    raise SystemExit(0)
raise SystemExit(process.wait())
PY
}

codex_run() {
  if [[ -n $TIMEOUT_BIN ]]; then "$TIMEOUT_BIN" "${STAGE_TIMEOUT:-3h}" codex "$@"; else codex "$@"; fi
}

schema_for() {
  case $1 in
    build) outcomes='["complete","incomplete","blocked"]' ;;
    review) outcomes='["approved","approved_with_notes","changes_required","incomplete","blocked"]' ;;
    qa) outcomes='["production_ready","ready_with_reservations","not_production_ready","incomplete","blocked"]' ;;
    pr) outcomes='["opened","ci_failed","conflict","incomplete","blocked"]' ;;
    *) echo "unknown stage: $1" >&2; return 64 ;;
  esac
  # reason is required but nullable, not optional: codex exec sends the schema
  # to the API with strict:true, and strict mode rejects optional properties.
  printf '{"type":"object","properties":{"outcome":{"enum":%s},"head_sha":{"type":"string","pattern":"^[0-9a-f]{7,64}$"},"reason":{"type":["string","null"]}},"required":["outcome","head_sha","reason"],"additionalProperties":false}' "$outcomes"
}

NOTE=""      # an extra line prepended to the next stage's prompt, used by /pr
stage_prompt() {
  local skill=$1 invocation
  if [[ $HARNESS == codex ]]; then
    invocation="\$$SKILL_NS:$skill $F"
  else
    invocation="/$SKILL_NS:$skill $F"
  fi
  printf '%s\n%s' "$invocation" "${NOTE}This is unattended run $RUN_ID, stage round $ROUND. Read lifecycle state from the default
checkout and feature artifacts from the feature worktree. Use the skill's full or
delta/retest mode for the current HEAD. Return exactly one structured outcome from
the supplied schema; include the feature HEAD as head_sha. Use incomplete only when
the same stage must resume, and blocked only for a decision the documents do not
answer - then name that decision in reason; otherwise set reason to null."
}

claude_stage() { # claude_stage <skill> <schema> <prompt> <permission flags...>
  local skill=$1 schema=$2 prompt=$3; shift 3
  claude_run -p "$prompt" \
    --max-turns "${MAX_TURNS:-400}" \
    --output-format stream-json --verbose --json-schema "$schema" "$@" \
  | tee -a "$D/loop.log" \
  | jq -r --unbuffered '
      if .type == "assistant" then (.message.content[]? | select(.type == "tool_use") | "   \(.name)")
      elif .type == "rate_limit_event" and .rate_limit_info.status == "rejected" then
        "RATE_LIMIT:\(.rate_limit_info.resetsAt // "")"
      elif .type == "result" then "RESULT:\(.structured_output.outcome //
            (if .subtype == "error_max_turns" then "incomplete" else "" end))\t\(.structured_output.head_sha // "")\t\(.structured_output.reason // "" | gsub("[\t\n\r]"; " "))"
      else empty end' \
  | { last=""
      while IFS= read -r line; do
        case $line in
          RATE_LIMIT:*) last=$(printf 'RATE_LIMIT\t%s' "${line#RATE_LIMIT:}") ;;
          RESULT:*) [[ $last == RATE_LIMIT$'\t'* ]] || last=${line#RESULT:} ;;
          *)         printf "%s\n" "$line" >&2 ;;
        esac
      done
      printf "%s\n" "$last"; }
}

codex_stage() { # codex_stage <skill> <schema> <prompt>
  local skill=$1 schema=$2 prompt=$3 status=0
  local schema_file="$RUN_TMP/$skill-schema.json"
  local result_file="$RUN_TMP/$skill-result.json"
  printf '%s\n' "$schema" > "$schema_file"
  : > "$result_file"
  codex_run exec --ephemeral --json --sandbox "${CODEX_SANDBOX:-workspace-write}" \
    --output-schema "$schema_file" --output-last-message "$result_file" "$prompt" \
  | tee -a "$D/loop.log" \
  | jq -r --unbuffered '
      if .type == "item.started" and .item.type == "command_execution" then
        "   shell"
      elif .type == "item.started" and .item.type == "mcp_tool_call" then
        "   \(.item.server // "mcp").\(.item.tool // "tool")"
      elif .type == "turn.failed" or .type == "error" then
        "   \(.error.message // .message // "Codex stage failed")"
      else empty end' >&2 || status=$?
  (( status == 0 )) || return "$status"
  jq -er '[.outcome, .head_sha, (.reason // "" | gsub("[\t\n\r]"; " "))] | @tsv' "$result_file"
}

stage() { # stage <skill> <permission flags...> -> tool calls to stderr, outcome and sha to stdout
  local skill=$1; shift
  local schema prompt
  schema=$(schema_for "$skill")
  echo "== $F: $skill" >&2
  prompt=$(stage_prompt "$skill")
  if [[ $HARNESS == codex ]]; then
    codex_stage "$skill" "$schema" "$prompt"
  else
    claude_stage "$skill" "$schema" "$prompt" "$@"
  fi
}

LOG_START=1                      # the log is appended across runs; summarise only ours
if [[ -f $D/loop.log ]]; then LOG_START=$(( $(wc -l < "$D/loop.log") + 1 )); fi
STAGES=0
RUN_STARTED=$SECONDS

# What the run cost, from the log it already writes. One session per stage, and a
# session's last result carries its totals - so take the last per session and add
# those up, never every result, or a stage that re-inited counts several times.
# shellcheck disable=SC2329  # invoked by the EXIT trap below
summary() {
  [[ -s $D/loop.log ]] || return
  local wall_minutes=$(( (SECONDS - RUN_STARTED) / 60 ))
  echo
  if [[ $HARNESS == codex ]]; then
    tail -n +"$LOG_START" "$D/loop.log" | jq -s -r --arg st "$STAGES" --arg wall "$wall_minutes" '
      [ .[] | select(.type == "turn.completed") ]
      | { turns: length,
          inp:   (map(.usage.input_tokens // 0) | add // 0),
          out:   (map(.usage.output_tokens // 0) | add // 0),
          cache: (map(.usage.cached_input_tokens // 0) | add // 0) }
      | "stages \($st) · Codex turns \(.turns) · actual wall clock \($wall) min",
        "tokens in \(.inp) · out \(.out) · cache read \(.cache)",
        "estimated cost unavailable in the Codex JSONL stream"'
  else
    tail -n +"$LOG_START" "$D/loop.log" | jq -s -r --arg st "$STAGES" --arg wall "$wall_minutes" '
      [ .[] | select(.type == "result") ] | group_by(.session_id) | map(max_by(.num_turns))
      | { turns: (map(.num_turns) | add // 0),
          min:   ((map(.duration_ms) | add // 0) / 60000 | floor),
          cost:  ((map(.total_cost_usd) | add // 0) * 100 | round / 100),
          inp:   (map(.usage.input_tokens // 0) | add // 0),
          out:   (map(.usage.output_tokens // 0) | add // 0),
          cache: (map(.usage.cache_read_input_tokens // 0) | add // 0) }
      | "stages \($st) · agent-reported \(.min) min · actual wall clock \($wall) min",
        "tokens in \(.inp) · out \(.out) · cache read \(.cache)",
        "estimated cost $\(.cost) - an estimate of API list price, not a subscription bill"'
  fi
}

cleanup() {
  summary
  rm -rf -- "$RUN_TMP"
  rm -f -- "$PID_FILE"
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

OUTCOME=""; HEAD_SHA=""; REASON=""; RATE_LIMITED=0; RATE_LIMIT_RESET=""
run() { # run <skill> <flags...> -> sets OUTCOME, HEAD_SHA and REASON
  local skill=$1 attempt=0 value delay
  shift
  STAGES=$((STAGES + 1))
  jq -nc --arg stage "$skill" --arg run "$RUN_ID" \
    '{type:"kaitersberg_stage", stage:$stage, run_id:$run}' >> "$D/loop.log"
  while :; do
    value=$(stage "$skill" "$@") || value=""
    if [[ $value == RATE_LIMIT$'\t'* ]]; then
      RATE_LIMITED=1
      RATE_LIMIT_RESET=${value#*$'\t'}
      return 0
    fi
    IFS=$'\t' read -r OUTCOME HEAD_SHA REASON <<<"$value" || true
    if [[ -n $OUTCOME ]]; then
      return 0
    fi
    attempt=$((attempt + 1))
    if (( attempt > INFRA_RETRIES )); then
      echo "$F: $skill returned no outcome after $INFRA_RETRIES retries - read $D/loop.log" >&2
      exit 3
    fi
    case $attempt in 1) delay=10 ;; 2) delay=30 ;; *) delay=60 ;; esac
    echo "$F: $skill had no outcome; transient retry $attempt/$INFRA_RETRIES in ${delay}s" >&2
    sleep "$delay"
  done
}

while :; do
  STATE_JSON=$(python3 "$STATE_HELPER" show "$STATE_FILE")
  CURRENT_STAGE=$(jq -r .stage <<<"$STATE_JSON")
  if [[ $CURRENT_STAGE == complete ]]; then
    echo "$F: this loop state is already complete"; exit 0
  fi
  MAX_ATTEMPTS=$(jq '[.attempts[]] | max // 0' <<<"$STATE_JSON")
  if (( MAX_ATTEMPTS >= ROUNDS )); then
    notify rounds_exhausted "$(jq -r '.attempts | to_entries | max_by(.value).key' <<<"$STATE_JSON")"
    echo "$F: persisted retry budget is exhausted ($MAX_ATTEMPTS/$ROUNDS); inspect the reports, raise ROUNDS or use LOOP_RESET=1" >&2
    exit 1
  fi
  if [[ $CURRENT_STAGE == pr && $PR != 1 ]]; then
    notify finished "stopped before PR (PR=0)"
    echo "$F: green after review and qa - next, by hand: /$SKILL_NS:pr $F"; exit 0
  fi
  ROUND=$(( $(jq -r --arg s "$CURRENT_STAGE" '.attempts[$s] // 0' <<<"$STATE_JSON") + 1 ))

  NOTE=""
  FLAGS=("${WRITE[@]}")
  if [[ $CURRENT_STAGE == review ]]; then
    FLAGS=("${READ[@]}")
    NOTE="Raw git and general shell commands are unavailable in this unattended
review. Use $REVIEW_GIT_HELPER --help and its fixed read-only queries for status,
diff, show, log, merge-base, worktree discovery, tracked files and grep. Pass that
same helper path to every review lane.
"
  fi
  if [[ $CURRENT_STAGE == pr ]]; then
    NOTE="A person started this run knowing it ends in a pull request. That is the
confirmation your rules require before pushing, given in advance for this feature
and this branch only. Do not stop to ask for it again. Do not merge.
"
  fi

  notify stage_started "$CURRENT_STAGE round $ROUND/$ROUNDS"
  run "$CURRENT_STAGE" "${FLAGS[@]}"
  if (( RATE_LIMITED )); then
    RATE_DETAIL="$CURRENT_STAGE rejected; resetsAt=${RATE_LIMIT_RESET:-unknown}"
    jq -nc --arg run "$RUN_ID" --arg feature "$F" --arg stage "$CURRENT_STAGE" \
      --arg reset "$RATE_LIMIT_RESET" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{type:"kaitersberg_rate_limit", run_id:$run, feature:$feature, stage:$stage,
        resets_at:(if $reset == "" then null else (($reset | tonumber?) // $reset) end),
        at:$at}' >> "$D/loop.log"
    notify rate_limited "$RATE_DETAIL"
    echo "$F: $RATE_DETAIL; persisted stage unchanged" >&2
    exit 3
  fi
  TRANSITION_ARGS=(transition "$STATE_FILE" "$CURRENT_STAGE" "$OUTCOME")
  if [[ -n $HEAD_SHA ]]; then TRANSITION_ARGS+=(--head-sha "$HEAD_SHA"); fi
  TRANSITION=$(python3 "$STATE_HELPER" "${TRANSITION_ARGS[@]}")
  ACTION=$(printf '%s' "$TRANSITION" | jq -r .action)
  COUNTER=$(printf '%s' "$TRANSITION" | jq -r '.counter // ""')
  ATTEMPTS=$(printf '%s' "$TRANSITION" | jq -r .attempts)
  NEXT_STAGE=$(printf '%s' "$TRANSITION" | jq -r .stage)

  jq -nc --arg run "$RUN_ID" --arg feature "$F" --arg stage "$CURRENT_STAGE" \
    --arg outcome "$OUTCOME" --arg head "$HEAD_SHA" --arg next "$NEXT_STAGE" \
    --arg action "$ACTION" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{type:"kaitersberg_transition", run_id:$run, feature:$feature, stage:$stage,
      outcome:$outcome, head_sha:($head | select(length > 0)), next_stage:$next,
      action:$action, at:$at}' >> "$D/loop.log"

  if [[ -n $STAGE_DONE_CMD ]]; then
    HOOK_STARTED=$SECONDS
    HOOK_CODE=0
    STAGE=$CURRENT_STAGE OUTCOME=$OUTCOME FEATURE=$F RUN_ID=$RUN_ID \
      HEAD_SHA=$HEAD_SHA NEXT_STAGE=$NEXT_STAGE ACTION=$ACTION \
      bash -c "$STAGE_DONE_CMD" || HOOK_CODE=$?
    HOOK_SECONDS=$((SECONDS - HOOK_STARTED))
    jq -nc --arg run "$RUN_ID" --arg feature "$F" --arg stage "$CURRENT_STAGE" \
      --arg outcome "$OUTCOME" --arg next "$NEXT_STAGE" --argjson code "$HOOK_CODE" \
      --argjson seconds "$HOOK_SECONDS" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{type:"kaitersberg_notification", run_id:$run, feature:$feature, stage:$stage,
        outcome:$outcome, next_stage:$next, exit_code:$code, duration_seconds:$seconds,
        at:$at}' >> "$D/loop.log"
    if (( HOOK_CODE != 0 )); then
      echo "$F: STAGE_DONE_CMD failed after $CURRENT_STAGE with exit $HOOK_CODE (ignored)" >&2
    fi
  fi

  notify stage_done "$CURRENT_STAGE round $ROUND/$ROUNDS: $OUTCOME"
  if [[ $ACTION == stop_blocked ]]; then
    notify decision_needed "${REASON:-$CURRENT_STAGE returned blocked - read $D/loop.log}"
    echo "$F: $CURRENT_STAGE needs a decision - read $D/loop.log"; exit 2
  fi
  if [[ -n $COUNTER && $ATTEMPTS -ge $ROUNDS ]]; then
    notify rounds_exhausted "$COUNTER"
    echo "$F: $COUNTER came back unfinished or red $ATTEMPTS times - read the current feature reports"; exit 1
  fi
  if [[ $ACTION == stop_ok ]]; then
    notify finished "PR opened"
    echo "$F: pull request opened and green - reading it and merging it are yours"; exit 0
  fi
done
