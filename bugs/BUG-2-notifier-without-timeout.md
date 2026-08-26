# BUG-2: A hanging notifier blocks the delivery loop without timeout(1)

**Status:** Open
**Severity:** Major
**Reported:** 2026-08-26 by review   **Affects:** users enabling `LOOP_NOTIFY` on systems without GNU timeout, including a default macOS installation
**Feature:** Delivery loop   **Branch:** muichdistl/fix-loop-review-findings

## Expected vs. observed
- **Expected:** `README.md` and `scripts/loop-feature.sh` say that a missing,
  failing or hanging notifier is reported and ignored because notification is not
  load-bearing.
- **Observed:** When neither `timeout` nor `gtimeout` exists, the notifier is run
  synchronously with no wall-clock bound.
- **Consequence:** One notifier that never returns prevents the current stage and
  every later delivery stage from running.

## Reproduction
1. Run the delivery loop with a `PATH` that contains its required commands but no
   `timeout` or `gtimeout`.
2. Set `LOOP_NOTIFY` to an executable that does not return.
3. Observe that the loop remains inside the first `stage_started` notification.
**Happens:** always when the notifier hangs and no timeout binary is installed
**Environment:** local macOS, Kaitersberg 0.5.2

## The loop
To be completed with the committed regression test and its failing output.

## Cause
To be completed after the regression test is red.

## Fix
To be completed after the cause is proven.

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | Notification execution stores no product records | No repair required |

## Also checked
Pending.

## Documents corrected
Pending.
