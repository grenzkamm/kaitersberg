---
name: build-loop
description: Run one planned feature unattended through isolated Build, Review, QA and optionally PR sessions, using the delivery runner bundled with this skill. Use when the user asks for the whole delivery loop rather than one stage.
---
<!-- Generated from .claude/skills/build-loop/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Build loop

## Role
You start and supervise the existing Kaitersberg delivery runner for one feature.
The runner owns the Build -> Review -> QA -> PR state machine and starts a fresh
harness process for every stage. You do not perform any of those stages yourself.

## Hard rules
- **Use the runner shipped with this skill.** Resolve the exact path of this loaded `SKILL.md` from Codex's skill catalog,
  then set `LOOP` to the `scripts/loop-feature.sh` file beside it. Do not
  infer the installed plugin root from the current repository or a cache path. The product
  repository does not contain this script, and a plugin cache or framework
  checkout path must never be guessed.
- **Run from the product repository's default checkout, never from a feature
  worktree or the Kaitersberg framework repository.** The runner creates and
  enters the feature worktree itself while lifecycle state stays on the default
  checkout. If the current directory is another worktree, use
  `git worktree list --porcelain` and the repository's default branch to locate
  the unique default checkout. Stop when it cannot be identified unambiguously.
- **One feature ID is required.** Accept only the repository's feature-ID shape,
  normally `PROJ-x`, and require exactly one matching directory below `features/`.
  Do not silently pick work for a command that can run for hours and open a pull
  request.
- **Starting this skill authorises the runner's PR stage for this feature.** Set
  `PR=0` only when the user asked to stop before the pull request. `$merge` is
  never part of this loop.
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
- The runner path does not exist or is not executable -> report the resolved path
  and stop; do not search caches or the product repository for another copy.
- The runner returns exit 2 (a product decision is needed) -> report the persisted
  stage and reason and stop. Do not answer the product question yourself.

---

## Phase 0 - Resolve the product and runner

```
🔁 Build loop: PROJ-x
```

Resolve the feature argument and the product repository's default checkout. Read
only the product context file's *Unattended runs* section and the matching feature
row to surface repository-specific controls; the runner and stage skills read the
rest when they need it.

Set `LOOP` exactly as required in the first hard rule. Verify `[ -x "$LOOP" ]`.

## Phase 1 - Start the loop

From the default checkout, run:

```bash
"$LOOP" PROJ-x
```

Pass through only environment overrides the user or product context supplied.
Keep the process attached and wait for its result unless the user explicitly asks
for a detached run. For a detached run use the product's documented supervisor
command; do not improvise a background process whose owner and logs disappear.

## Phase 2 - Report the handoff

Report the runner's exit meaning and the path it printed for persisted state:

- exit 0: delivery reached PR, or stopped before PR because `PR=0`;
- exit 1: a findings budget was exhausted;
- exit 2: a person must decide something the plans do not answer;
- exit 3: infrastructure or harness failure, including capacity rejection.

Include the current stage, the next operator action and the runner's bounded cost
summary. Do not call a stopped or rate-limited run complete.

## Checklist
- [ ] Bundled runner resolved without a product or cache path guess
- [ ] Command started from the product default checkout
- [ ] Exactly one explicit feature ID selected
- [ ] User/product environment overrides preserved, none invented
- [ ] Fresh-process stage isolation left to the runner
- [ ] Exit, persisted stage and next action reported
- [ ] `$merge` not started
