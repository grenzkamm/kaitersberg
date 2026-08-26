# BUG-4: The status template points at the wrong source for feature scope

**Status:** Open
**Severity:** Minor
**Reported:** 2026-08-26 by review   **Affects:** status-page runs after the 0.5.2 token-cost change
**Feature:** Status skill   **Branch:** muichdistl/fix-loop-review-findings

## Expected vs. observed
- **Expected:** The status skill says feature scope comes from the scope section
  of `features/INDEX.md`, without opening each `spec.md` for that value.
- **Observed:** Its mandatory HTML template still asks for "the scope line from
  spec.md".
- **Consequence:** A status run must either violate the skill's bounded reading
  rule or ignore the template it is required to fill.

## Reproduction
1. Compare the scope-source instruction in `.claude/skills/status/SKILL.md` with
   the placeholder in `.claude/skills/status/template.md`.
2. Observe that the former names `features/INDEX.md` and the latter names
   `spec.md`.
**Happens:** always in Kaitersberg 0.5.2
**Environment:** repository source and every generated plugin bundle

## The loop
To be completed with the committed contract test and its failing output.

## Cause
To be completed after the regression test is red.

## Fix
To be completed after the cause is proven.

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | Documentation only | No repair required |

## Also checked
Pending.

## Documents corrected
Pending.
