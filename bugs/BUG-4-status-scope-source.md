# BUG-4: The status template points at the wrong source for feature scope

**Status:** Closed
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
- **Command:** `python3 -m unittest tests.test_skill_contracts.SkillContractTest.test_bug_4_status_template_uses_the_board_scope_line -v`
- **Asserts:** the authored template names `features/INDEX.md`, not `spec.md`, as
  the source of a feature's scope line.
- **Failing output:**
  ```text
  AssertionError: 'the scope line from spec.md' unexpectedly found in
  '.claude/skills/status/template.md'

  Ran 1 test in 0.001s
  FAILED (failures=1)
  ```
- **Minimised to:** the one semantic placeholder shared by every generated status
  template.

## Cause
- **Candidates considered:**
  1. The authored template was omitted when the status skill's read source changed.
  2. The generated Codex or plugin trees were stale.
  3. The status skill still required spec scope in another phase.
- **In one sentence:** the source skill changed to board scope, but its authored
  output template retained the old `spec.md` placeholder and the generator
  correctly copied that contradiction everywhere.
- **Where:** `.claude/skills/status/template.md`
- **Same cause also reached through:** the generated Codex port and both plugin
  bundles, all derived from that one source.

## Fix
- **What changed:** the authored template now names `features/INDEX.md`; the Codex
  port and both plugin bundles were regenerated, and both plugin versions moved to
  0.6.1.
- **Where:** `.claude/skills/status/template.md` and its generated copies
- **Regression test:** `BUG-4 status template uses the board scope line` - source
  contract, seen failing first

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | Documentation only | No repair required |

## Also checked
`python3 scripts/port-to-codex.py --check` proves all generated trees match the
authored source. The skill linter and both manifest checks pass.

## Documents corrected
| Document | What was wrong or missing |
|---|---|
| `.claude/skills/status/template.md` | Named `spec.md` after the skill moved the scope source to `features/INDEX.md` |
