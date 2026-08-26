#!/usr/bin/env bash
#
# loop-status.sh [PROJ-x] [--follow]
#
# The read-only status of the delivery loops scripts/loop-feature.sh persisted
# in this product repository: one block per feature with loop state below Git's
# common directory, or only the named feature. --follow then tails the loops'
# event streams (<feature>/loop.log) and prints new kaitersberg events as they
# arrive; ctrl-c leaves the loops untouched.
#
# Read-only means read-only: no lock is taken, no state or repository file is
# written, and git is used only for fixed queries - the same philosophy as
# scripts/review-git.py. What is shown is what the loop persisted, including its
# recorded ROUNDS budget, not this shell's environment.
#
set -euo pipefail

F=""
FOLLOW=0
for arg in "$@"; do
  case $arg in
    --follow) FOLLOW=1 ;;
    *)
      [[ $arg =~ ^[A-Za-z]+-[0-9]+$ && -z $F ]] \
        || { echo "usage: $0 [PROJ-x] [--follow]" >&2; exit 64; }
      F=$arg
      ;;
  esac
done
command -v jq >/dev/null || { echo "jq is required" >&2; exit 69; }

GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null) \
  || { echo "run this inside a product repository" >&2; exit 64; }
[[ $GIT_COMMON == /* ]] || GIT_COMMON=$(pwd)/$GIT_COMMON
STATE_DIR=$GIT_COMMON/kaitersberg/loops
# The default checkout is where the loop runs and writes <feature>/loop.log; a
# linked worktree has the same folders but not the log, so resolve to the main
# working tree rather than to wherever this command happens to run.
ROOT=$(dirname "$GIT_COMMON")

shopt -s nullglob
if [[ -n $F ]]; then
  STATES=("$STATE_DIR/$F.json")
  [[ -f ${STATES[0]} ]] || { echo "no loop state for $F below $STATE_DIR"; exit 0; }
else
  STATES=("$STATE_DIR"/*.json)
  ((${#STATES[@]})) \
    || { echo "no loop state below $STATE_DIR - no unattended run has started here"; exit 0; }
fi

loop_pid() { # best effort, the same ps query buzz-doctor.py uses; no pid is persisted
  ps -axo pid=,command= 2>/dev/null \
    | awk -v f="$1" '$0 ~ /loop-feature\.sh/ && $0 ~ ("(^| )" f "( |$)") {print $1; exit}' \
    || true
}

mtime() { # file modification time, BSD stat first, then GNU
  stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%S' "$1" 2>/dev/null \
    || stat -c '%y' "$1" 2>/dev/null || echo "?"
}

for state_file in "${STATES[@]}"; do
  STATE=$(cat "$state_file")
  feature=$(jq -r '.feature // empty' <<<"$STATE")
  [[ -n $feature ]] || feature=$(basename "$state_file" .json)
  stage=$(jq -r .stage <<<"$STATE")
  outcome=$(jq -r '.last_outcome // "none yet"' <<<"$STATE")
  rounds=$(jq -r '.rounds // "?"' <<<"$STATE")
  max_attempts=$(jq '[.attempts[]] | max // 0' <<<"$STATE")
  attempt=$(jq -r --arg s "$stage" '.attempts[$s] // 0' <<<"$STATE")
  updated=$(jq -r '.updated_at // "?"' <<<"$STATE")

  pid=$(loop_pid "$feature")
  lock="not held"
  [[ -d $STATE_DIR/$feature.lock ]] && lock="held ($STATE_DIR/$feature.lock)"

  if [[ $stage == complete ]]; then
    verdict="finished"
  elif [[ -n $pid ]]; then
    verdict="running"
  elif [[ $outcome == blocked ]]; then
    verdict="stopped: decision needed"
  elif [[ $rounds =~ ^[0-9]+$ ]] && (( max_attempts >= rounds )); then
    verdict="stopped: rounds exhausted"
  else
    verdict="stale: no loop process, state not terminal"
  fi

  round=$((attempt + 1))
  if [[ $rounds =~ ^[0-9]+$ ]] && (( round > rounds )); then round=$rounds; fi

  last_event="$updated (state)"
  logs=("$ROOT"/features/"$feature"-*/loop.log)
  if ((${#logs[@]})) && [[ -f ${logs[0]} ]]; then
    last_event="$(mtime "${logs[0]}") (loop.log)"
  fi

  # Fixed read-only queries only: list the worktrees, then read one HEAD.
  head_line="no feature worktree"
  worktree=""
  while IFS= read -r line; do
    case $line in
      "worktree "*) worktree=${line#worktree } ;;
      "branch refs/heads/feature/$feature" | "branch refs/heads/feature/$feature-"*)
        head_line=$(git -C "$worktree" log -1 --format='%s (%cr)' 2>/dev/null) \
          || head_line="worktree at $worktree is unreadable"
        break
        ;;
    esac
  done < <(git worktree list --porcelain 2>/dev/null)

  printf '%s  %s\n' "$feature" "$verdict"
  if [[ $stage == complete ]]; then
    printf '  stage       complete\n'
  else
    printf '  stage       %s (round %s/%s)\n' "$stage" "$round" "$rounds"
  fi
  printf '  last        %s at %s\n' "$outcome" "$updated"
  process="none"
  [[ -z $pid ]] || process="pid $pid alive"
  printf '  process     %s\n' "$process"
  printf '  lock        %s\n' "$lock"
  printf '  last event  %s\n' "$last_event"
  printf '  worktree    %s\n' "$head_line"
  echo
done

((FOLLOW)) || exit 0

FOLLOW_LOGS=()
for state_file in "${STATES[@]}"; do
  feature=$(jq -r '.feature // empty' "$state_file")
  [[ -n $feature ]] || feature=$(basename "$state_file" .json)
  for log in "$ROOT"/features/"$feature"-*/loop.log; do FOLLOW_LOGS+=("$log"); done
done
((${#FOLLOW_LOGS[@]})) || { echo "no loop.log to follow below $ROOT/features"; exit 0; }

echo "following ${FOLLOW_LOGS[*]} - ctrl-c stops watching, never the loop" >&2
# tail's file headers and the raw harness events fail fromjson? or the select
# and disappear; only the loop's own kaitersberg events are printed.
tail -n 0 -f "${FOLLOW_LOGS[@]}" | jq -Rr --unbuffered '
  fromjson? | select((.type // "") | startswith("kaitersberg"))
  | if .type == "kaitersberg_stage" then
      "run \(.run_id // "?")  \(.stage) started"
    elif .type == "kaitersberg_transition" then
      "\(.at // "?")  \(.feature // "?")  \(.stage): \(.outcome) -> \(.next_stage)"
    elif .type == "kaitersberg_notification" then
      "\(.at // "?")  \(.feature // "?")  STAGE_DONE_CMD after \(.stage) exited \(.exit_code)"
    else tojson end'
