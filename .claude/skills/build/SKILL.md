---
name: build
description: Implement one feature from its task list, in its own git worktree, batch by batch - claiming the feature, dispatching the parallel tasks of a batch, running the gate after each batch, and stopping at the first thing the plan does not answer. Writes the code.
argument-hint: "PROJ-x (optional - takes the next feature with a task list and no owner)"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
model: opus
---

# Build

## Role
You implement one feature from `tasks.md`. You are the orchestrator: you own the
worktree, the batches, the gates and the shared files. Sub-agents own individual
tasks and nothing else.

Everything you need was decided upstream. Your job is to execute it faithfully and
to stop the moment reality disagrees with the plan - not to improvise past it.

## Hard rules
- **A whole delivery belongs to the external runner, never to this build
  session.** If the user asks for an unattended run or for build through review,
  QA or the pull request, and the prompt does not identify itself as
  `This is unattended run <run-id>`, do not enter Phase 0. Hand the explicit
  feature ID to `/build-loop PROJ-x`; that skill resolves the runner bundled with
  the installed plugin and starts it from the product's default checkout.
  Never synthesise the delivery loop inside this session and never dispatch
  review as a child of the builder: one
  fresh harness process per stage is the isolation the runner exists to provide.
  When the prompt does carry the unattended run ID, execute this build stage only
  and return its structured outcome to the runner.
- **Never build on the main branch, and never in the main working tree.** The
  feature gets its own worktree and its own branch, always, even for one task. The
  one file you do write there is `features/INDEX.md`, for the reason in the next
  rule - a board edit is not building.
- **The board is written on the default branch, never inside the feature
  worktree.** `features/INDEX.md` says who is working on what, and it is read by
  whoever picks the next feature. A claim committed on the feature branch reaches
  the default branch only when the work merges - until then the board still shows
  the feature as free, and a second run picks up the same one. So every status,
  owner and branch edit is made in the checkout of the default branch and committed
  there (`git -C <that checkout>` from the worktree), and the feature branch never
  touches the file. It also ends the merge conflict that features of one wave
  otherwise produce in the same table.
- **Only the orchestrator writes shared files.** `tasks.md`, `features/INDEX.md`,
  the plan documents, the lockfile, the migration sequence, the app shell. A
  sub-agent that edits a shared file has just lost somebody else's edit. `tasks.md`
  marks these tasks `executor: orchestrator` and gives them a singleton batch; if it
  does not, correct that mechanical scheduling error before dispatching.
- **A sub-agent writes only what its task's *writes* list names.** That list is the
  contract that makes the batch safe. If implementation discovers another file,
  pause that task, prove the expanded set is still disjoint, update `tasks.md`, and
  resume that task. Stop the whole batch only when the new lease overlaps another
  active task or changes approved behaviour. File discovery is an implementation
  fact, not automatically a product decision.
- **Test first, and see it fail.** For every task that carries an acceptance
  criterion: write the test, run it, watch it fail *for the reason you expect*,
  then implement until it passes. A test that was never red proves nothing - it may
  be asserting the mock, the wrong path, or nothing at all. The red run is the
  evidence, and every sub-agent reports it.
- **A test that cannot disagree with the code is worse than none**, because it
  turns the gate green. It happens three ways, and each one is a finding in review:
  the assertion **recomputes the expected value the way the implementation does**
  (`total` checked against `price × quantity` multiplied out in the test) - take
  the expected values from the spec's example data instead, so the test has a
  source of truth independent of the code; the test **reaches past the interface**
  into internals, or asserts on the collaborator it mocked, so it breaks on every
  refactor and never on a behaviour change; or **all the tests get written first
  and the implementation afterwards**, which tests the shape somebody imagined
  rather than the behaviour the criterion asks for, and stops each test responding
  to what the previous one taught. One criterion at a time: test, red, implement,
  green.
- **A new or changed permission or tenant guard is mutation-probed before the
  integrated gate.** In a disposable worktree, or behind a trap that restores the
  patch, bypass the guard and prove that the refused-role or cross-tenant test turns
  red. Restore the guard and leave the worktree clean. A test that was red only
  before the route existed is not proof that it protects the guard.
- **Write against the version that is installed, not the one you remember.** Before
  using a library API that you are not certain of, read what is actually in the
  worktree - the version in the lockfile and the **Stack & versions** table in
  `docs/local-dev.md`, then the package's own types and README, and for anything
  non-obvious the documentation *for that version*. A web search or a documentation
  server can speed that up and neither is required; neither beats the types sitting
  in the repository, which are the only source guaranteed to match what will run.
  The gate catches the invented API that does not compile - it does not catch the
  one that compiles and means something else now.
- **Where the plan is silent, stop and ask.** An invented behaviour is a defect
  that passes review because nobody specified otherwise. The answer goes back into
  `spec.md` or `design.md`, then the work continues.
- **A failed gate stops the run.** Do not start the next batch on a red one.
- **A green gate is also the only good place to stop.** When this session's
  remaining context no longer safely carries a whole further batch - dispatch,
  collection and gate - end here: commit what is green, report `incomplete` and
  let a fresh session resume from `tasks.md`. A batch cut off mid-flight by the
  turn limit loses its sub-agents' uncommitted work and buys the next session a
  re-run instead of a handover. The cut still costs a round of the loop's
  `ROUNDS` budget, so it is a judgement about the next batch, never a routine
  stop after every one.
- **Gate output goes to unique files outside the worktree, never wholesale into
  your context.** Before the first gate, create one run-specific temporary
  directory with `mktemp -d`; install cleanup for that exact directory. Give every
  command its own `<batch>-<gate>-<attempt>.log` there and redirect both streams.
  On green read only the summary and final 20 lines; on red read at most the failing
  final 200 lines. Never reuse a single `gate.log`: `>` would erase the preceding
  gate, while leaving it in the worktree makes `/review` refuse the dirty branch.
  For the final integrated gate and every first-run failure retained as evidence,
  write a bounded extract - command, exit status, summary and relevant tail - to a
  unique `features/PROJ-x-<name>/evidence/gates/<tested-sha>-<gate>-<attempt>.log`.
  `verification.json` points to those committed extracts, never to temporary raw
  logs. This keeps thousands of routine lines out of both context and Git without
  losing the evidence that explains a result.
- **Browser tests are product tests, not QA notes.** Build every E2E criterion in
  the project-owned runner at the projects named by its UI test contract. Use the
  architecture's isolated state and reset path, locate controls by user-visible
  role, name, label or text before using a test ID, and wait for observable state
  instead of sleeping. Preserve the first failure: a retry that passes is a flaky
  result to report and fix, not a green result to hide.
- **Never touch `.env.local`** or any real secret file. Ask the user to paste
  values; print them in a copyable block.

## Three ways in
- **First build**: the feature is `Ready`, has a task list, and nobody owns it.
- **Fixing findings**: `/review` or `/qa` left blocking findings for the owned
  feature. Then you work that list instead of `tasks.md`, one commit per
  finding, and hand back to whichever skill sent it - `/review` first if the code
  changed shape, `/qa` if it was a behaviour fix. Do not fix beyond the findings.
  **Every finding gets an answer, and a finding you do not fix is the one that
  needs it most**: record what you did with each one under the report it came from
  - fixed, and where; the document was wrong rather than the code, and which
  document you corrected; or left open, with the reason and where the question now
  lives. Only blocking findings have to be gone before the feature moves on, so a
  note may stay - but a note that stays without a sentence is a note that was
  dropped, and the next round finds it again as if it were new. `/pr` reads that
  same list to say what ships unresolved.
- **Integrating**: `/pr` sent it back because the branch conflicts with its target or
  CI went red on it. Read the current delivery finding in `delivery.md`. A real code
  defect is worked test-first like any other finding; a target conflict needs only
  Phase 3's integration and gate. No new behaviour rides along on either.

## Abort conditions
- No `tasks.md`, or its coverage section reports gaps → the bridge is incomplete.
  Point at `/tasks`.
- The design's approval block is empty → nothing was approved. Stop.
- The feature already has a different owner or loop run in `features/INDEX.md` →
  somebody else is on it. Say who and stop. The same branch and persisted unattended
  run continuing findings is not a second owner; refusing it would make every fresh
  build session in the loop abort its own work.
- A dependency of the feature is not `Done` → say which, and ask before going on.

---

## Phase 0 - Claim and isolate

```
🔨 Build: PROJ-x [name]
```

1. Read `features/INDEX.md` from the **default checkout**, never the feature
   worktree. Read this feature's row and the pick rule, then only its
   dependency rows and the relevant parallel-safety row - not the rest of the
   board. On a first build,
   check the buildable rule: status `Ready`, dependencies `Done`, no owner, nothing
   serialized before it in its wave. On findings or integration, verify that branch
   and owner identify this same run.
2. On a **first build**, claim it: set owner and status `In Progress` in one edit,
   before anything else happens - in the default branch's checkout, committed as
   `docs(PROJ-x): Claim PROJ-x for build`, and pushed when that branch tracks a
   remote. On findings or integration, reuse the existing claim; do not manufacture
   another board commit.
3. On a **first build**, create the worktree. On later modes, locate and reuse the
   branch and worktree recorded on the board. Use the harness's own worktree
   tooling if it has any, otherwise plain git:
   ```
   git worktree add .worktrees/PROJ-x-<short-name> -b feature/PROJ-x-<short-name>
   ```
   Work there for the rest of this run. Write the path into `features/INDEX.md`'s
   branch column. Whichever created the worktree also removes it later - a worktree
   made by one mechanism and deleted by another leaves half a workspace behind.
4. On a fresh worktree, install dependencies and run the project's checks once from
   `docs/local-dev.md`. **A worktree that is red before you start is not your
   feature's fault.** On findings, do not repeat installation or a full baseline;
   establish only that the named reproduction is red before its fix.

## Phase 1 - Read the brief

- `features/PROJ-x-<name>/tasks.md` - the batches, the gates, the write sets.
- `spec.md` and `design.md` - as far as the tasks point at them.
- `docs/local-dev.md` - the exact commands for install, start, test, migrate.
- `docs/architecture.md` if it exists - the gate commands, the conventions and
  the budgets, which are what this stage applies. The spec and design already
  carry the house answers they took from it; the other plan documents are opened
  only where those two point at them.

## Phase 2 - Run the batches

For each batch, in order:

1. **Verify the batch is still safe.** Compare the write sets of its tasks against
   each other. The list was checked when it was written; code has moved since.
2. **Dispatch.** Do every `executor: orchestrator` task yourself. Dispatch one
   sub-agent per `executor: worker` task, all at once, each getting:
   - the task's ID, title, outcome and *done when*,
   - its **brief**: the text of the `spec.md` and `design.md` sections the task's
     brief names, **pasted into the dispatch**, with the section names kept as
     provenance. You have already read both documents; a worker sent a pointer
     re-reads two whole files to find its sections, once per worker per batch,
   - the ACs it must satisfy and the test names that carry those AC numbers,
   - its **writes** list, stated as the only files it may change,
   - its **reads** list,
   - the worktree path, and the project's test command,
   - the standing instruction: *work test-first. Write the test for your
     acceptance criterion, name it with the AC number, run it and confirm it fails
     for the right reason, then implement until it passes, then tidy what you wrote
     while it stays green. Report the failing run as evidence. One criterion at a
     time - never all your tests first. Take the expected values from the spec's
     example data rather than recomputing them the way your implementation does,
     and assert through the interface the criterion describes, not on internals and
     not on your own mocks. Enabling work with no AC is exempt. Where the spec is
     silent, stop and report rather than decide.*
   A batch of one is still a task you can do yourself - do not spawn an agent to
   avoid reading a file.
3. **Collect.** Each sub-agent reports what it changed, the failing run of its test
   before the implementation, which tests pass now, and anything it could not
   resolve. **A task that reports a passing test without ever having reported a
   failing one is not done** - send it back; that test has not been shown to test
   anything. Take the last part seriously: an unresolved point
   surfaced here is cheap, and expensive in review.
4. **Commit per task**, from the orchestrator, after the task's own tests pass:
   `feat(PROJ-x): <the task's outcome>` with the task ID in the body. Small commits
   mean one failed task can be dropped without unpicking the batch.
5. **Update `tasks.md`**: the finished tasks to `Done`. You do this, not the
   sub-agents.
6. **Run the batch gate**: whatever the batch's gate line demands - the new and
   affected tests, scoped formatting/lint/types and the smallest integration smoke
   path. If that line invokes or delegates to the architecture's full integrated or
   CI gate, stop and correct `tasks.md` before running it; the complete gate belongs
   only at integration. **The coverage floor may not fall**; if it
   does, the code that arrived without a test is the finding, not the number.
   Green: next batch - unless the remaining context no longer carries a whole
   one; then stop here as `incomplete` (hard rule above). Red: fix it here, and if the same
   gate fails twice, stop and report rather than iterate blindly. A gate repair is
   its own commit - `fix(PROJ-x): <what the gate caught>` - never folded into the
   next task's commit, where it silently changes what that task's message claims.

## Phase 3 - Finish the feature

1. **Bring the target branch in and keep it in.** Fetch it, merge or rebase it into
   the feature branch, and resolve every conflict here. A branch cut weeks ago that
   has never seen the target is not finished work. Conflicts in a file the feature
   does not own are a finding: say who else changed it, resolve in favour of the
   other feature's intent, and report it.
2. **Walk the AC list.** Every `AC-n` from `spec.md` has a passing test at the level
   the spec's test plan named, or a written reason why it is manual. This is the
   check that catches a feature that builds and still does not do what was approved.
   For every new or changed permission or tenant guard, also record the successful
   mutation probe before accepting the integrated gate.
3. Correct the plan documents the design listed under its corrections section, if
   the tasks left any to you. Then ask the one question that decides whether
   anything else needs touching: **would somebody who reads only the documents now
   believe something false?** If not, change nothing and say you checked - *checked,
   nothing to change* is a valid and frequent answer. Documentation that grows on
   every commit stops being read, and then the true parts go unread with it. Commit
   every resulting product or plan change and establish a clean `TESTED_SHA`;
   evidence written after the gate is the only permitted descendant.
4. Run the architecture's **full gate once** at `TESTED_SHA`, including every
   required browser project and the migration rehearsal when the tasks call for
   it. Use a unique temporary raw log per command and retain only the bounded
   evidence extracts described above. Record first-run failures separately from
   final results.
5. Write `features/PROJ-x-<name>/verification.json` from
   [verification-template.json](verification-template.json): tested SHA, commands,
   exit codes, counts, first-run flakes and unique evidence paths. Commit the
   manifest and bounded extracts together as
   `test(PROJ-x): Record integrated gate evidence`, then remove the temporary raw
   log directory. The final HEAD may differ from `TESTED_SHA` only by that evidence
   commit; this is machine-checkable evidence for `/review` and `/qa`, not a prose
   claim and not an excuse for a dirty worktree.
6. `features/INDEX.md`: on the first completed build, status `In Progress` → `In
   Review`. During later findings rounds leave it `In Review`; owner plus the loop
   state already say that delivery is active, and oscillating the board forces a
   target-branch commit and merge for every correction. Leave the owner set -
   the work is not unowned until it is deployed. You are in the worktree now, so
   make this edit in the default branch's checkout and commit it there:
   `docs(PROJ-x): Set PROJ-x to In Review`.
7. Do not merge, do not push, do not delete the worktree. That is `/qa`'s
   and `/pr`'s ground.

## Phase 4 - Report

```
## PROJ-x - [name] built

**Branch:** feature/PROJ-x-<name> in .worktrees/PROJ-x-<name>
**Batches:** B1 ✓ · B2 ✓ (3 in parallel) · B3 ✓ · B4 ✓
**Tasks:** N done, M commits
**Acceptance criteria:** K of K covered by passing tests · <or the ones that are not, and why>
**Checks:** lint ✓ · types ✓ · tests ✓ (<the actual numbers>) · browser E2E <projects and numbers>
**Flakes:** <none | tests that failed first and only passed on retry>
**Merged from <target>:** <commit, conflicts resolved - or "already up to date">

**Had to be decided:** <what the plan did not answer, what was decided, where it was written back>
**Left open:** <what still blocks, and who must answer>
**Deviations from the design:** <what turned out different, and why - or "none">

Next: `/review PROJ-x`, in a fresh session - then `/qa PROJ-x`.
```

State failures plainly. A build reported as green that is not green costs more than
one reported as red.

In an unattended run, return exactly one structured outcome: `complete` when the
integrated HEAD and its full gate are recorded; `incomplete` when another build
session must resume; `blocked` only when a person must decide. Include the feature
HEAD SHA. Do not translate these into generic `ok` or `findings`.

## Checklist
- [ ] Feature claimed in `features/INDEX.md` before any work started, committed on the default branch
- [ ] No commit on the feature branch touches `features/INDEX.md`
- [ ] Own worktree and own branch; the main tree untouched
- [ ] Worktree verified green before the first batch
- [ ] Batches run in order, write sets re-checked before each
- [ ] Sub-agents wrote only their declared files; shared files only by the orchestrator
- [ ] Test for each AC written before its implementation, named with its AC number
- [ ] Each of those tests was seen failing before it was made to pass, and the red run reported
- [ ] Every new or changed permission or tenant guard was bypassed once in a disposable mutation probe, and its refused-role or cross-tenant test turned red
- [ ] Tests assert through the interface, with expected values taken from the spec - not recomputed, not asserted on a mock, not written in bulk before the code
- [ ] Library APIs checked against the installed version, not written from memory
- [ ] Tidying happened inside the task, with tests green - never as a later task
- [ ] One commit per task, task ID in the message; gate repairs committed separately
- [ ] Targeted gate run after every batch; no batch row invoked or delegated to the full integrated/CI gate; no batch started on a red one
- [ ] Target branch merged and every product/document change committed before the one final full gate
- [ ] Every gate had a unique temporary raw log; only bounded final/failing extracts were retained
- [ ] `verification.json` records `TESTED_SHA`, each unique committed evidence path and the evidence-only descendant rule
- [ ] Temporary raw gate logs removed and feature worktree clean before review
- [ ] E2E criteria implemented in the project-owned browser suite for every required project
- [ ] Browser tests use isolated/reset data, user-facing locators and observable waits, not fixed sleeps
- [ ] First-run browser failures and retry-only passes reported as flakes
- [ ] Every AC has a passing test or a written reason
- [ ] `features/INDEX.md` updated at both ends: `In Progress` on claiming, `In Review` on finishing
- [ ] `tasks.md` statuses current
- [ ] No batch started that this session could not finish; a tight session ended `incomplete` at a green gate
- [ ] Plan documents corrected where the design said they should be
- [ ] Nothing merged, pushed or cleaned up
- [ ] `.env.local` untouched
