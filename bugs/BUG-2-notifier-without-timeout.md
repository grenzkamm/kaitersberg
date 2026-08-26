# BUG-2: A hanging notifier blocks the delivery loop without timeout(1)

**Status:** Reproduced
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
- **Command:** `python3 -m unittest tests.test_loop_feature.FeatureLoopTest.test_bug_2_hanging_notifier_is_bounded_without_timeout_binary -v`
- **Asserts:** a hanging notifier is terminated and ignored when the machine has
  no `timeout` or `gtimeout` executable.
- **Failing output:**
  ```text
  subprocess.TimeoutExpired: Command '[.../scripts/loop-feature.sh, PROJ-7]'
  timed out after 1.5 seconds

  Ran 1 test in 1.529s
  FAILED (errors=1)
  ```
- **Minimised to:** one fake product, one blocked fake stage, an isolated command
  path without timeout and a notifier whose only child sleeps.

## Cause
- **Candidates considered:**
  1. The shared `notify()` path has no portable fallback when coreutils is absent.
  2. Timeout detection selects the wrong executable on macOS.
  3. The ntfy example is the only notifier whose own client timeout made the
     documented contract appear true.
- **In one sentence:** `notify()` ran its executable directly whenever coreutils
  was absent, and terminating only the notifier would still leave child processes
  holding the loop's output pipes open.
- **Where:** `scripts/loop-feature.sh`, `notify()`
- **Same cause also reached through:** all seven notification sites; they all use
  the shared function and need no caller-specific guard.

## Fix
- **What changed:** Notifications run through the already-required Python runtime
  with a 30-second default bound. Each notifier gets its own process group so a
  timeout terminates its children too; failures remain reported and ignored.
- **Where:** the shared `notify()` function in `scripts/loop-feature.sh`
- **Regression test:** `BUG-2 hanging notifier is bounded without timeout binary`
  - command integration, seen timing out before the fix and green afterwards

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | Notification execution stores no product records | No repair required |

## Also checked
Successful, failing and missing notifiers still preserve the loop result. Claude
and Codex stage runs, blocked decisions, exhausted rounds and PR completion remain
green in the full 42-test suite.

## Documents corrected
| Document | What was wrong or missing |
|---|---|
| None | `README.md` and the script comments already promised bounded, non-load-bearing notification; the implementation was wrong |
