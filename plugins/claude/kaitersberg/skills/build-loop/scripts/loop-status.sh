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
# written, and git is used only for fixed queries - the same philosophy as the
# bundled review-git.py. What is shown is what the loop persisted, including its
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

detached_record() { # detached_record <feature> [have_state] - latest durable launcher result
  local feature=$1 have_state=${2:-} log exit_file code
  local logs=("$STATE_DIR/$feature"-*.detached.log)
  ((${#logs[@]})) || return 1
  log=${logs[$((${#logs[@]} - 1))]}
  exit_file=${log%.detached.log}.detached.exit
  if [[ -f $exit_file ]]; then
    IFS= read -r code < "$exit_file" || code="unreadable"
    printf '%s  detached launcher exited %s\n' "$feature" "$code"
  elif [[ -n $have_state ]]; then
    # The state block above already says what is known; the launcher's
    # "current state unknown" would contradict it line for line. Its log still
    # carries the full harness output of the running stage, so keep that pointer.
    printf '  launcher log   %s\n' "$log"
    return 0
  else
    printf '%s  detached launcher accepted; current state unknown\n' "$feature"
  fi
  printf '  launcher log   %s\n' "$log"
  printf '  launcher exit  %s\n' "$exit_file"
}

contains() { # contains <needle> [values...]
  local needle=$1 value
  shift
  for value in "$@"; do
    [[ $value == "$needle" ]] && return 0
  done
  return 1
}

DETACHED_ONLY=()
if [[ -n $F ]]; then
  STATES=("$STATE_DIR/$F.json")
  if [[ ! -f ${STATES[0]} ]]; then
    detached_record "$F" || echo "no loop state for $F below $STATE_DIR"
    exit 0
  fi
else
  # Only feature-shaped names are state files; the same directory legitimately
  # holds other JSON - backups and other tools' per-attempt snapshots - whose
  # shape the jq queries below would crash on.
  STATES=()
  for state in "$STATE_DIR"/*.json; do
    [[ ${state##*/} =~ ^[A-Za-z]+-[0-9]+\.json$ ]] && STATES+=("$state")
  done
  DETACHED_LOGS=("$STATE_DIR"/*.detached.log)
  for log in "${DETACHED_LOGS[@]}"; do
    filename=${log##*/}
    [[ $filename =~ ^([A-Za-z]+-[0-9]+)-.*\.detached\.log$ ]] || continue
    feature=${BASH_REMATCH[1]}
    [[ -f $STATE_DIR/$feature.json ]] && continue
    contains "$feature" "${DETACHED_ONLY[@]}" || DETACHED_ONLY+=("$feature")
  done
  ((${#STATES[@]} + ${#DETACHED_ONLY[@]})) \
    || { echo "no loop state below $STATE_DIR - no unattended run has started here"; exit 0; }
fi

loop_pid() { # repository-bound: loop-feature writes this product's pid beside its lock
  local feature=$1 pid_file=$STATE_DIR/$1.pid pid command
  [[ -d $STATE_DIR/$1.lock ]] || return 0
  [[ -f $pid_file ]] || return 0
  IFS= read -r pid < "$pid_file" || return 0
  [[ $pid =~ ^[0-9]+$ ]] || return 0
  kill -0 "$pid" 2>/dev/null || return 0
  command=$(ps -p "$pid" -o command= 2>/dev/null) || return 0
  [[ $command =~ loop-feature\.sh ]] || return 0
  [[ $command =~ (^|[[:space:]])$feature([[:space:]]|$) ]] || return 0
  printf '%s\n' "$pid"
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
  feature_worktree=""
  while IFS= read -r line; do
    case $line in
      "worktree "*) worktree=${line#worktree } ;;
      "branch refs/heads/feature/$feature" | "branch refs/heads/feature/$feature-"*)
        feature_worktree=$worktree
        head_line=$(git -C "$worktree" log -1 --format='%s (%cr)' 2>/dev/null) \
          || head_line="worktree at $worktree is unreadable"
        break
        ;;
    esac
  done < <(git worktree list --porcelain 2>/dev/null)

  # Task progress from the feature's tasks.md: the build maintains the Status
  # column in its worktree, so that copy is current while a worktree exists;
  # before the claim and after the merge the default checkout's copy is.
  # ponytail: trusts the bundled template's column order (status second-to-last,
  # owner last) - a reshaped table drops the line rather than breaking the block.
  tasks_files=()
  [[ -n $feature_worktree ]] \
    && tasks_files+=("$feature_worktree"/features/"$feature"-*/tasks.md)
  tasks_files+=("$ROOT"/features/"$feature"-*/tasks.md)
  tasks_line=""
  for tasks_md in "${tasks_files[@]}"; do
    [[ -f $tasks_md ]] || continue
    tasks_line=$(awk -F'|' -v f="$feature" '
      $2 ~ "^[[:space:]]*" f "-T[0-9]+[[:space:]]*$" {
        total++
        status = $(NF-2); gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
        id = $2; gsub(/^[[:space:]]+|[[:space:]]+$/, "", id)
        if (status == "Done") finished++
        else if (status == "In Progress")
          active = active (active == "" ? "" : ", ") id
      }
      END {
        if (!total) exit
        line = finished "/" total " done"
        if (active != "") line = line ", in progress: " active
        print line
      }' "$tasks_md")
    break
  done

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
  [[ -z $tasks_line ]] || printf '  tasks       %s\n' "$tasks_line"
  detached_record "$feature" have_state || true
  echo
done

for feature in "${DETACHED_ONLY[@]}"; do
  detached_record "$feature"
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
