---
name: pr
description: Open the pull request for a finished feature - a body assembled from the spec, design, review and test report, with the acceptance criteria, the migration, the new configuration, the security result and a runbook the reviewer can actually follow. Confirms before pushing.
---
<!-- Generated from .claude/skills/pr/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Pull Request

## Role
You write the pull request that closes one feature. It is the last document
somebody reads before the code becomes everybody's problem, and the first one they
will read again in a year when something breaks.

Everything in it already exists in the feature folder. Your job is to assemble it
honestly, not to write a new account of the work.

## Hard rules
- **Assembled from the artifacts, never from memory.** Every claim in the body
  traces to `spec.md`, `design.md`, `review.md`, `qa.md` or the diff. If the test
  report says a criterion is not automatically testable, the body says that too.
- **Read only the current review and QA snapshots.** Historical rounds under
  `evidence/report-history/` are available for audit and delta verification, but
  are not PR inputs unless the current snapshot links one as evidence.
- **Never overstate the state.** A body claiming green while a check is red is
  worse than no body: it teaches the next reviewer not to read yours.
- **Confirm before pushing.** Show the body, name the branch and the target, and
  wait. Pushing and opening a pull request is outward-facing and irreversible in
  the eyes of everybody watching the repository.
- **One feature, one pull request.** An unrelated fix that snuck into the branch
  either gets its own, or gets named in the body as what it is.
- **Do not merge, and do not move the board.** Merging is somebody's decision and
  belongs to `$merge`, which also sets `Done` and cleans up. This skill opens the
  pull request and stops there.
- **Delivery failures are a typed handoff, not a dead end.** A target conflict or
  red CI writes the current `delivery.md` on the feature branch with the failing
  check, evidence and tested SHA. `$build` consumes it, and the unattended loop has
  a real return path instead of exiting after an unclassified finding.

## Abort conditions
- `qa.md` missing, or its verdict is *Not production ready* → nothing to open yet.
  Say which finding decides it. **The foundation feature `PROJ-1` is the one
  exception**: it has no acceptance criteria and `$qa` does not run for it, so
  `features/PROJ-1-scaffold/proof.md` takes the place of the test report and its
  `review.md` is still required. Without that proof file there is nothing to open
  either.
- `review.md` says `Changes required` and the findings are not addressed → same.
- The branch has uncommitted changes → commit or explain them first; a pull request
  that does not match the working tree is a lie with a diff attached.
- The branch has not seen the target branch since it last moved, or merging it
  conflicts → replace `delivery.md` from
  [delivery-template.md](delivery-template.md), record the conflicting paths,
  target SHA and feature HEAD SHA, and send it back to
  `$build`. Resolving a conflict here means resolving it without the tests that were
  run against the result. An unattended run returns `conflict`, not an empty result.

**The target branch** - the *base* referred to throughout - is the default branch
unless `features/INDEX.md` records another one for this feature's wave. Name it
explicitly in the report; every diff, log and check below is measured against it.

---

## Phase 0 - Check the state

```
🔀 PR: PROJ-x [name]
```

1. From `features/INDEX.md`, read only this feature's row: status `In Review`, owner
   and branch set. Use the pick rule only when eligibility itself is in question.
2. `review.md` verdict and `qa.md` verdict - both must allow it.
3. `git status` in the worktree, `git log <base>..HEAD`, and the full diff stat.
4. Whether a remote and a pull request tool exist at all (`git remote -v`,
   `gh auth status`). If not, write the body to
   `features/PROJ-x-<name>/pr.md` and hand it to the user instead of guessing.

## Phase 1 - Assemble the body

Use [template.md](template.md). Take each part from where it already lives:

| Section | Comes from |
|---|---|
| What and why | `spec.md` - the *Why* section, in two sentences |
| Scope, and what is deliberately not in it | `spec.md` - scope, including its "not" half |
| Acceptance criteria | `qa.md` - the per-criterion verdict table, condensed. For `PROJ-1`: the proof table from `proof.md` instead, labelled as what it is |
| How to verify it yourself | `docs/local-dev.md` plus the spec's example data |
| Data and migration | `design.md` - fields, status values, migration, reversibility |
| Roles and permissions | `design.md` - the admin/user table, only the rows that changed |
| Personal data | `spec.md` - classification, legal basis, retention, erasure |
| Security | `design.md` protections plus the adversarial result from `qa.md` |
| Configuration, environment, dependencies | `design.md` - every new one, and who must set it |
| Screens | `evidence/` - the screenshots and the recording |
| Deviations and decisions | `build`'s report, `review.md`, the design's corrections section |
| Risk and rollback | `design.md` - effect on existing data, reversibility |
| Open follow-ups | Whatever `review.md` and `qa.md` left as notes |

**The runbook is the part reviewers actually use, so write it for somebody who has
not seen this feature**: check out the branch, install, migrate, seed, log in as
which role, do exactly these steps, expect exactly this. Include the one path that
proves it works and the one that proves it refuses.

**Follow-ups get an ID.** A leftover named in prose is forgotten by Friday. Either
it becomes a row in `features/INDEX.md` with its own `PROJ-y`, or it is not a
follow-up, it is an omission - say which.

## Phase 2 - Keep the commits readable

The commits already carry the task IDs from `$build`. Leave them: one commit per
task, each traceable to acceptance criteria, is a better history than one squashed
lump nobody can bisect. If the branch collected fixup noise while findings were
worked, tidy that - never the task commits themselves.

Title: `feat(PROJ-x): <the outcome, in the words of the spec>`.

## Phase 3 - Confirm, then open

Show the user the finished body, the branch, the target branch and the commit
count. Ask whether to push and open it.

On yes:
```
git push -u origin feature/PROJ-x-<short-name>
gh pr create --title "<title>" --body-file features/PROJ-x-<name>/pr.md --base <target>
```
Keep the body in the feature folder as `pr.md` - the pull request will be closed one
day and its description with it; the folder stays.

On no: leave `pr.md` written and say what would have been run.

**Then watch the checks you just started.** `gh pr checks <n> --watch`, or the run
list if the harness has no such command. CI is the only place this code runs on a
machine that is not the one that wrote it, and a pull request opened with a red
pipeline hands the reviewer a debugging session instead of a review. Red: report
which check failed with its log line, replace
`features/PROJ-x-<name>/delivery.md` from
[delivery-template.md](delivery-template.md), and send the feature back to `$build`
- do not "fix it quickly" here, this skill fixes nothing. On green, replace that
file with a short resolved record so an old failure cannot be mistaken for current
work. No CI configured at all: say that in the report rather than leaving the line
empty.

## Phase 4 - Report

```
## PROJ-x - [name]

**Pull request:** <url, or "not opened, body at features/PROJ-x-<name>/pr.md">
**Branch:** feature/PROJ-x-<name> → <target>   **Commits:** N   **Diff:** +A −B across C files
**Acceptance criteria:** K of K passing · <the manual ones named>
**CI:** <check names and results - or "no CI configured">
**Needs before deploy:** <environment variables, migration, configuration - or "nothing">
**Follow-ups filed:** <PROJ-y …, or "none">

Next: `$merge PROJ-x` once it is reviewed and approved - it merges and clears
the worktree, the branches and the board.
```

In an unattended run, return exactly one structured outcome: `opened` only when
the pull request exists and its required CI is green; `ci_failed`; `conflict`;
`incomplete` when the same stage must resume watching; or `blocked` for a human
decision. Include the feature HEAD SHA.

## Checklist
- [ ] Both verdicts checked before anything was written
- [ ] Every claim in the body traced to an artifact, none written from memory
- [ ] Acceptance criteria table complete, manual ones marked as manual
- [ ] Runbook written for somebody who has never seen the feature
- [ ] Migration, configuration, environment variables and new dependencies named
- [ ] Personal data and security results carried over, not summarised away
- [ ] Screenshots or recording linked from `evidence/`
- [ ] Deviations from the design stated, including the ones nobody objected to
- [ ] Follow-ups filed as `PROJ-y` rows, not left in prose
- [ ] Title carries the feature ID; commits left task-shaped
- [ ] User confirmed before the push
- [ ] CI checks watched after the push and their result reported; red sends the feature back
- [ ] Red CI or a conflict recorded as the current `delivery.md`; green replaces it with a resolved record
- [ ] Body kept as `features/PROJ-x-<name>/pr.md`
- [ ] Nothing merged, and no rung moved - `$merge` owns both
