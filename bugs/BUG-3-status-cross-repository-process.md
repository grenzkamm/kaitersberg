# BUG-3: loop-status mistakes a loop from another repository for the local loop

**Status:** Fixed
**Severity:** Minor
**Reported:** 2026-08-26 by review   **Affects:** users with two product repositories containing the same feature ID
**Feature:** Delivery loop   **Branch:** muichdistl/fix-loop-review-findings

## Expected vs. observed
- **Expected:** `README.md` says `scripts/loop-status.sh` reports the persisted
  loops of the product repository in which it is run.
- **Observed:** Process discovery scans the whole machine for
  `loop-feature.sh <feature-id>` without tying the process to this repository.
- **Consequence:** A stale local `PROJ-7` state is reported as running whenever a
  different repository currently runs its own `PROJ-7`.

## Reproduction
1. Create a stopped loop state for a feature in one temporary repository.
2. Start an unrelated process whose command line contains the same feature ID.
3. Run `loop-status.sh` in the stopped repository and observe `running`.
**Happens:** always while the foreign same-ID process exists
**Environment:** local macOS, Kaitersberg 0.5.2

## The loop
- **Command:** `python3 -m unittest tests.test_loop_status.LoopStatusTest.test_bug_3_same_feature_process_from_another_repo_is_not_running -v`
- **Asserts:** a same-ID loop process without this repository's lock and PID record
  cannot make a stopped local state read as running.
- **Failing output:**
  ```text
  AssertionError: 'stale: no loop process' not found in
  'LST-41  running ... process pid 10885 alive ... lock not held'

  Ran 1 test in 0.242s
  FAILED (failures=1)
  ```
- **Minimised to:** one temporary repository with persisted state and one foreign
  process whose command contains the same feature ID.

## Cause
- **Candidates considered:**
  1. The system-wide process scan is not tied to the repository whose state is read.
  2. Status gives process detection precedence over the persisted blocked or
     exhausted outcome.
  3. The displayed lock is not used to establish process ownership.
- **In one sentence:** status selected the first machine-wide command containing
  `loop-feature.sh` and the feature ID even though no local lock owned that PID.
- **Where:** `scripts/loop-status.sh`, `loop_pid()`
- **Same cause also reached through:** every feature ID reported by the status
  command; the process lookup is shared.

## Fix
- **What changed:** the loop records its shell PID beside the repository-specific
  lock and removes it during cleanup. Status requires that lock and PID record,
  verifies the live command and never scans unrelated processes.
- **Where:** lock lifecycle in `scripts/loop-feature.sh` and `loop_pid()` in
  `scripts/loop-status.sh`
- **Regression test:** `BUG-3 same feature process from another repo is not
  running` - command integration, seen reporting running before the fix and green
  afterwards

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | The defect only misreports live status | No repair required |

## Also checked
A positive test proves that a matching PID beside the local lock still reports
`running`. Graceful completion removes the PID record. Stale, blocked, exhausted,
finished and missing-state views remain covered.

## Documents corrected
| Document | What was wrong or missing |
|---|---|
| None | `README.md` already scoped status to the current product repository; process discovery violated it |
