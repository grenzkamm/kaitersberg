#!/usr/bin/env bash
#
# loop-feature.sh PROJ-x
#
# Drives one feature through /build -> /review -> /qa without a person in the
# chair, and stops where the framework wants one. Run it in the *product*
# repository, not here, with the kaitersberg plugin installed.
#
# Every stage is its own `claude -p` process. That is the load-bearing part:
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
# can follow along with
#   tail -f features/PROJ-x-*/loop.log | jq -r 'select(.type=="assistant")'
#
# Outliving the window: every stage is a child of the shell that started this, so
# closing the terminal - or ending the agent session that started it for you - kills
# the stage in flight with its work uncommitted. Detach it if that matters:
#   tmux new -d -s PROJ-x 'ROUNDS=3 scripts/loop-feature.sh PROJ-x'
#
# Being told when it ends: the script only reports an exit code, on purpose -
# wrap it in whatever already notifies you, for example
#   ntfy done -- scripts/loop-feature.sh PROJ-3
# Being told per stage: set STAGE_DONE_CMD to a shell command; it runs after every
# stage outcome and its persisted transition with STAGE, OUTCOME, FEATURE, RUN_ID,
# HEAD_SHA, NEXT_STAGE and ACTION in its environment. A failing hook is recorded,
# reported and ignored - notification is never load-bearing.
#   STAGE_DONE_CMD='curl --fail-with-body -sS -o /dev/null -X POST https://relay/hooks/<id> -H "X-Webhook-Secret: <s>"' \
#     scripts/loop-feature.sh PROJ-3
# Exit codes: 0 green, 1 no green result, 2 a decision is needed, 3 a run failed.
# Spend is not capped here: the runs go through the subscription. MAX_TURNS is
# what stops a stage that circles - 400, because /qa on a feature with 57
# acceptance criteria ran out at 200 with its report written and the board not yet
# moved. Reaching it is not a failure: the stage goes round again.
#
#   PR=0 scripts/loop-feature.sh PROJ-3   # ... and stop before the pull request
#
set -euo pipefail

F=${1:-}
[[ $F =~ ^[A-Za-z]+-[0-9]+$ ]] || { echo "usage: $0 PROJ-x" >&2; exit 64; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 69; }

# macOS ships no `timeout`; coreutils installs it as `gtimeout`. Without either,
# run uncapped rather than not at all - --max-turns still bounds a stage that
# circles, it just takes longer to say so.
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || echo "")
[[ -n $TIMEOUT_BIN ]] || echo "note: no timeout(1) found, stages run without a wall clock" >&2

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
mkdir -p "$STATE_DIR"
mkdir "$LOCK_DIR" 2>/dev/null || {
  echo "$F already has a loop lock at $LOCK_DIR" >&2; exit 75;
}
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

if [[ ${LOOP_RESET:-0} == 1 && -f $STATE_FILE ]]; then
  mv "$STATE_FILE" "$STATE_FILE.$(date -u +%Y%m%dT%H%M%SZ).bak"
fi

RUN_ID=${RUN_ID:-"$(date -u +%Y%m%dT%H%M%SZ)-$$"}
START_STAGE=${START_STAGE:-build}
python3 "$STATE_HELPER" init "$STATE_FILE" "$F" "$RUN_ID" --stage "$START_STAGE" >/dev/null
RUN_ID=$(python3 "$STATE_HELPER" show "$STATE_FILE" --field run_id)

# /build dispatches its tasks as background subagents, and `claude -p` kills those
# ten minutes after its own turn ends - which is how the first PROJ-3 run lost an
# unfinished task with its work uncommitted. 0 means wait for them.
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS:-0}

ROUNDS=${ROUNDS:-3}  # maximum persisted red/incomplete outcomes per stage
PR=${PR:-1}          # open the pull request after QA allows delivery; PR=0 stops before it
SKILL_NS=${SKILL_NS:-kaitersberg}
INFRA_RETRIES=${INFRA_RETRIES:-3}
STAGE_DONE_CMD=${STAGE_DONE_CMD:-}  # per-stage notification hook, see header

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
READ=(--permission-mode dontAsk --allowedTools "Read,Glob,Grep,Bash($REVIEW_GIT_HELPER *),Agent,Edit(features/**/review.md)")

claude_run() {
  if [[ -n $TIMEOUT_BIN ]]; then "$TIMEOUT_BIN" "${STAGE_TIMEOUT:-3h}" claude "$@"; else claude "$@"; fi
}

schema_for() {
  case $1 in
    build) outcomes='["complete","incomplete","blocked"]' ;;
    review) outcomes='["approved","approved_with_notes","changes_required","incomplete","blocked"]' ;;
    qa) outcomes='["production_ready","ready_with_reservations","not_production_ready","incomplete","blocked"]' ;;
    pr) outcomes='["opened","ci_failed","conflict","incomplete","blocked"]' ;;
    *) echo "unknown stage: $1" >&2; return 64 ;;
  esac
  printf '{"type":"object","properties":{"outcome":{"enum":%s},"head_sha":{"type":"string","pattern":"^[0-9a-f]{7,64}$"}},"required":["outcome","head_sha"],"additionalProperties":false}' "$outcomes"
}

NOTE=""      # an extra line prepended to the next stage's prompt, used by /pr
stage() { # stage <skill> <permission flags...> -> tool calls to stderr, outcome and sha to stdout
  local skill=$1; shift
  local schema
  schema=$(schema_for "$skill")
  echo "== $F: $skill" >&2
  claude_run -p "/$SKILL_NS:$skill $F
${NOTE}This is unattended run $RUN_ID. Read lifecycle state from the default
checkout and feature artifacts from the feature worktree. Use the skill's full or
delta/retest mode for the current HEAD. Return exactly one structured outcome from
the supplied schema; include the feature HEAD as head_sha. Use incomplete only when
the same stage must resume, and blocked only for a decision the documents do not
answer." \
    --max-turns "${MAX_TURNS:-400}" \
    --output-format stream-json --verbose --json-schema "$schema" "$@" \
  | tee -a "$D/loop.log" \
  | jq -r --unbuffered '
      if .type == "assistant" then (.message.content[]? | select(.type == "tool_use") | "   \(.name)")
      elif .type == "result" then "RESULT:\(.structured_output.outcome //
            (if .subtype == "error_max_turns" then "incomplete" else "" end))\t\(.structured_output.head_sha // "")"
      else empty end' \
  | { last=""
      while IFS= read -r line; do
        case $line in
          RESULT:*) last=${line#RESULT:} ;;
          *)         printf "%s\n" "$line" >&2 ;;  # the live ticker
        esac
      done
      printf "%s\n" "$last"; }
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
}

cleanup() {
  summary
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

OUTCOME=""; HEAD_SHA=""
run() { # run <skill> <flags...> -> sets OUTCOME and HEAD_SHA
  local skill=$1 attempt=0 value delay
  shift
  STAGES=$((STAGES + 1))
  jq -nc --arg stage "$skill" --arg run "$RUN_ID" \
    '{type:"kaitersberg_stage", stage:$stage, run_id:$run}' >> "$D/loop.log"
  while :; do
    value=$(stage "$skill" "$@") || value=""
    OUTCOME=${value%%$'\t'*}
    if [[ $value == *$'\t'* ]]; then HEAD_SHA=${value#*$'\t'}; else HEAD_SHA=""; fi
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
  CURRENT_STAGE=$(python3 "$STATE_HELPER" show "$STATE_FILE" --field stage)
  if [[ $CURRENT_STAGE == complete ]]; then
    echo "$F: this loop state is already complete"; exit 0
  fi
  MAX_ATTEMPTS=$(python3 "$STATE_HELPER" show "$STATE_FILE" \
    | jq '[.attempts[]] | max // 0')
  if (( MAX_ATTEMPTS >= ROUNDS )); then
    echo "$F: persisted retry budget is exhausted ($MAX_ATTEMPTS/$ROUNDS); inspect the reports, raise ROUNDS or use LOOP_RESET=1" >&2
    exit 1
  fi
  if [[ $CURRENT_STAGE == pr && $PR != 1 ]]; then
    echo "$F: green after review and qa - next, by hand: /$SKILL_NS:pr $F"; exit 0
  fi

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

  run "$CURRENT_STAGE" "${FLAGS[@]}"
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

  if [[ $ACTION == stop_blocked ]]; then
    echo "$F: $CURRENT_STAGE needs a decision - read $D/loop.log"; exit 2
  fi
  if [[ -n $COUNTER && $ATTEMPTS -ge $ROUNDS ]]; then
    echo "$F: $COUNTER came back unfinished or red $ATTEMPTS times - read the current feature reports"; exit 1
  fi
  if [[ $ACTION == stop_ok ]]; then
    echo "$F: pull request opened and green - reading it and merging it are yours"; exit 0
  fi
done
