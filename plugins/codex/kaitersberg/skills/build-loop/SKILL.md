---
name: build-loop
description: Start or inspect one planned feature's unattended Build, Review, QA and optional PR loop using the runtime bundled with this skill. Use for a whole delivery, a detached run, or loop status; not for one delivery stage.
---
<!-- Generated from .claude/skills/build-loop/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Build loop

## Role
You start or inspect the existing Kaitersberg delivery runner for one feature. The
runner owns the Build -> Review -> QA -> PR state machine and starts a fresh harness
process for every stage. You do not perform any of those stages yourself.

## Hard rules
- **Use the runtime shipped with this skill.** Resolve the exact directory containing this loaded `SKILL.md` from Codex's
  skill catalog. Set `LOOP` to its `scripts/loop-feature.sh` and `STATUS` to
  its `scripts/loop-status.sh`, and set `DETACH` to its
  `scripts/loop-detach.sh`. The product
  repository contains none of these scripts, and a plugin cache or framework
  checkout path must never be guessed.
- **Run from the product repository's default checkout, never from a feature
  worktree or the Kaitersberg framework repository.** The runner creates and
  enters the feature worktree itself while lifecycle state stays on the default
  checkout. If the current directory is another worktree, use
  `git worktree list --porcelain` and the repository's default branch to locate
  the unique default checkout. Stop when it cannot be identified unambiguously.
- **One feature ID is required.** Accept only the repository's feature-ID shape,
  normally `PROJ-x`, and require exactly one matching directory below `features/`.
  The optional mode is exactly one of `detached`, `status` or `follow`; no mode
  means an attached run. Do not silently pick work for a command that can run for
  hours and open a pull request.
- **Starting an attached or detached run authorises the runner's PR stage for this
  feature.** Set `PR=0` only when the user asked to stop before the pull request.
  Status and follow modes authorise no delivery action. `$merge` is never part of
  this loop.
- **A detached start is not a completed delivery.** A successful
  `tmux new-session -d` means only that tmux accepted the session. Report the
  detached handoff and stop; never interpret that exit code with the runner's exit
  table.
- **Preserve stage isolation.** Invoke the runner once; never replace it with
  child agents or a handwritten sequence of `$build`, `$review`, `$qa` and `$pr`.
- **Do not invent environment overrides.** Preserve explicit settings such as
  `KAITERSBERG_HARNESS`, `ROUNDS`, `PR`, `START_STAGE`, `LOOP_RESET`,
  `INFRA_RETRIES` and `LOOP_NOTIFY`. Let the runner's documented defaults apply
  when the user did not set them.
- **Never touch `.env.local`** or any real secret file.

## Abort conditions
- No feature ID, more than one matching feature folder, or no match -> report the
  exact problem and stop.
- The product default checkout cannot be identified uniquely -> show the
  candidate worktrees and stop.
- Any bundled runtime script does not exist or is not executable -> report all
  three resolved paths and stop; do not search caches or the product repository
  for another copy.
- Detached mode without `tmux`, or with an existing `kaitersberg-PROJ-x` session
  -> report the condition and stop. Never replace or join an existing session as
  if a new run had started.
- The runner returns exit 2 (a product decision is needed) -> report the persisted
  stage and reason and stop. Do not answer the product question yourself.

---

## Phase 0 - Resolve the product and runtime

```
🔁 Build loop: PROJ-x
```

Resolve the feature argument and the product repository's default checkout. Read
only the product context file's *Unattended runs* section and the matching feature
row to surface repository-specific controls; the runner and stage skills read the
rest when they need it.

Set `LOOP`, `STATUS` and `DETACH` exactly as required in the first hard rule and
verify all three are executable. Resolve the absolute state path as
`<git-common-dir>/kaitersberg/loops/PROJ-x.json` and the absolute event-log path as
`<default-checkout>/<feature-folder>/loop.log`. The state or log may not exist yet
before a detached child finishes initialising; their paths are still deterministic.

## Phase 1 - Run the selected mode

For `status` or `follow`, inspect the existing loop without starting one:

```bash
"$STATUS" PROJ-x
"$STATUS" PROJ-x --follow
```

For the default attached mode, run from the default checkout and wait for the
runner process itself to end:

```bash
"$LOOP" PROJ-x
```

For `detached`, run the bundled launcher from the default checkout:

```bash
"$DETACH" PROJ-x
```

It owns the deterministic tmux session, passes the explicit runner environment and
captures the child's complete output and final exit code below Git's common
directory. Do not recreate its tmux command in this skill.

## Phase 2 - Report the handoff

For status and follow, report only what the bundled status helper observed.

For an attached run, and only after the runner process itself ended, report its
exit meaning:

- exit 0: delivery reached PR, or stopped before PR because `PR=0`;
- exit 1: a findings budget was exhausted;
- exit 2: a person must decide something the plans do not answer;
- exit 3: infrastructure or harness failure, including capacity rejection.

Include the current stage, the next operator action and the runner's bounded cost
summary plus the state and event-log paths printed by the runner. Do not call a
stopped or rate-limited run complete.

For a detached run, use a separate **Detached handoff**. Do not apply the runner
exit table. Report exactly `accepted; current state unknown` until the status
helper shows either persisted runner state or a durable launcher exit. Then report:

- the `kaitersberg-PROJ-x` tmux session name;
- the absolute state and event-log paths resolved in Phase 0;
- the launcher log and exit-code paths printed by `DETACH`, which remain after an
  immediately failed pane disappears;
- `tmux attach-session -t '=kaitersberg-PROJ-x'` while the session still exists;
- `"$STATUS" PROJ-x` for a snapshot; and
- `"$STATUS" PROJ-x --follow` for the event stream.

## Checklist
- [ ] Bundled runner, detached launcher and status helper resolved without a path guess
- [ ] Command started from the product default checkout
- [ ] Exactly one explicit feature ID selected
- [ ] User/product environment overrides preserved, none invented
- [ ] Fresh-process stage isolation left to the runner
- [ ] Attached runner exit interpreted only after that process ended
- [ ] Detached start reported as accepted, never as completed
- [ ] Session, state, event-log, launcher log and exit-code paths reported when detached
- [ ] `$merge` not started
