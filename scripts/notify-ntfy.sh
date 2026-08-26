#!/usr/bin/env bash
#
# notify-ntfy.sh <feature> <event> <detail>
#
# An EXAMPLE LOOP_NOTIFY notifier that posts one loop event to an ntfy topic.
# The loop itself knows no vendor - that is deliberate, and this file is the
# smallest working bridge to one, never a default. Use it like this:
#
#   NTFY_TOPIC=my-loop LOOP_NOTIFY=<framework>/scripts/notify-ntfy.sh \
#     scripts/loop-feature.sh PROJ-3
#
# NTFY_SERVER overrides the public https://ntfy.sh instance for a self-hosted
# one. Exit codes do not matter to the loop: a failure is reported and ignored.
#
set -euo pipefail

FEATURE=${1:?usage: notify-ntfy.sh <feature> <event> <detail>}
EVENT=${2:?usage: notify-ntfy.sh <feature> <event> <detail>}
DETAIL=${3:-}
: "${NTFY_TOPIC:?NTFY_TOPIC must name the ntfy topic to post to}"

curl -fsS --max-time 10 -o /dev/null \
  -H "Title: $FEATURE $EVENT" \
  -d "$DETAIL" \
  "${NTFY_SERVER:-https://ntfy.sh}/$NTFY_TOPIC"
