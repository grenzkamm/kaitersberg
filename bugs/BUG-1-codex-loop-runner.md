# BUG-1: Codex invents an in-session delivery loop instead of using the runner

**Status:** Reproduced
**Severity:** Major
**Reported:** 2026-08-25 by Markus   **Affects:** Codex users running an unattended feature delivery
**Feature:** Delivery loop   **Branch:** muichdistl/fix-BUG-1-codex-loop-runner

## Expected vs. observed
- **Expected:** `README.md` says that `scripts/loop-feature.sh PROJ-x` runs build,
  review, QA and optionally the pull request in separate unattended sessions for
  the supported host.
- **Observed:** In the Codex loop test, Codex did not use the script and assembled
  its own loop inside the active session.
- **Consequence:** Review is no longer independent from the build session, runner
  state and retry limits are bypassed, and the documented unattended contract is
  not exercised.

## Reproduction
1. Start an unattended feature delivery from Codex.
2. Observe that no `codex exec` stage process is started by
   `scripts/loop-feature.sh`; Codex orchestrates the stages itself.
**Happens:** always when the runner is selected for Codex
**Environment:** local, Codex CLI 0.149.1, Kaitersberg 0.5.0

## The loop
- **Command:** `python3 -m unittest tests.test_loop_feature.FeatureLoopTest.test_codex_runner_drives_each_stage_with_codex_exec`
- **Asserts:** selecting Codex makes every delivery stage a separate `codex exec`
  invocation through `scripts/loop-feature.sh`.
- **Failing output:**
  ```text
  AssertionError: Lists differ: [] != ['complete', 'approved',
  'production_ready', 'opened']

  Ran 1 test in 1.787s
  FAILED (failures=1)
  ```
- **Minimised to:** one fake product repository, the real loop script and four
  deterministic fake stage outcomes.

## Cause
- **Candidates considered:**
  1. The runner is hard-coded to `claude -p` and Claude's event format; selecting
     Codex therefore has no effect.
  2. The build skill has no entry rule that redirects a requested whole delivery
     to the external runner, so an interactive Codex session synthesises one.
  3. The documentation claims host parity although only the skill trees, not the
     unattended runner, were ported.
  4. Replacing the executable alone would fail because Codex uses different
     schema, JSONL and permission flags.
- **In one sentence:** pending reproduction
- **Where:** pending reproduction
- **Same cause also reached through:** pending caller trace

## Fix
- **What changed:** pending
- **Where:** pending
- **Regression test:** `BUG-1 Codex runner drives each stage with codex exec` -
  command integration, pending first red run

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | The defect changes orchestration only | No product data is stored by this repository |

## Also checked
Pending.

## Documents corrected
| Document | What was wrong or missing |
|---|---|
| Pending | Pending cause analysis |
