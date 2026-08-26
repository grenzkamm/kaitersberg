# BUG-3: loop-status mistakes a loop from another repository for the local loop

**Status:** Open
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
To be completed with the committed regression test and its failing output.

## Cause
To be completed after the regression test is red.

## Fix
To be completed after the cause is proven.

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | The defect only misreports live status | No repair required |

## Also checked
Pending.

## Documents corrected
Pending.
