# BUG-1: Codex invents an in-session delivery loop instead of using the runner

**Status:** Fixed
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
- **In one sentence:** The unattended runner implemented only Claude's process and
  event protocol, while the build skill did not distinguish a whole-delivery
  request from one build stage, leaving Codex to invent its own orchestration.
- **Where:** `scripts/loop-feature.sh` and `.claude/skills/build/SKILL.md`
- **Same cause also reached through:** harness detection, stage invocation,
  structured-result parsing, cost summaries, dashboard child-process detection and
  the unattended-run documentation.

## Fix
- **What changed:** The runner now selects Claude or Codex explicitly or from its
  parent session. Codex stages run as independent `codex exec --ephemeral`
  processes with a JSON Schema and persisted JSONL events. The build skill now
  hands a whole-delivery request to the documented external script and forbids an
  in-session replacement loop.
- **Where:** `scripts/loop-feature.sh`, `.claude/skills/build/SKILL.md` and their
  generated ports; supporting documentation and dashboard process recognition were
  corrected with them.
- **Regression test:** `BUG-1 Codex runner drives each stage with codex exec` -
  command integration, seen failing before the fix and green afterwards

## Existing damage
| Records affected | State now | What was done |
|---|---|---|
| None | The defect changes orchestration only | No product data is stored by this repository |

## Also checked
The explicit Codex selection and automatic detection from a parent Codex session
both drive separate build, review, QA and pull-request processes. The existing
Claude path, persisted retries, resume behavior, notifications and stage
transitions remain covered. `scripts/check.sh` passed with all 32 tests, every
ShellCheck and Python check, the generated-port check and both plugin manifests at
version 0.5.1. No product records or existing loop state require repair.

## Documents corrected
| Document | What was wrong or missing |
|---|---|
| `README.md` | Claimed Codex support while showing only a harness-neutral-looking command backed by a Claude-only implementation; also overstated Codex's enforceable review allowlist |
| `.claude/skills/build/SKILL.md` | Did not say that whole delivery requests must enter through the external runner |

`docs/process.md` was checked; its process-level statement that unattended stages
use separate sessions remains true and needs no change.
