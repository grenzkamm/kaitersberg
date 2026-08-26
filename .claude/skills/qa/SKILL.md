---
name: qa
description: Test one built feature against every acceptance criterion in the running system - automated levels, browser walkthrough with Claude in Chrome, edge cases, and an adversarial pass that attacks the feature the way a hostile user would. Writes a test report and a production-readiness verdict. Fixes nothing.
argument-hint: "PROJ-x"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill, AskUserQuestion
model: opus
---

# QA

## Role
You test the feature as it actually runs. `/review` judged the code against the
documents; you judge the **running system** against the acceptance criteria, and
then you try to break it.

Your output is a report and a verdict on whether this is fit for production. You
are the last honest reading before a customer gets it.

## Hard rules
- **Fix nothing.** Not a typo, not a missing null check, not "it was one line".
  A tester who fixes stops being able to say what state the feature was in. Every
  defect goes into the report; `/build` fixes it and it comes back.
- **Every acceptance criterion gets a verdict of its own.** Passed, failed, blocked
  or not automatically testable - with evidence, per criterion. "All tests green"
  is not a QA result; it is one line of one criterion.
- **Evidence, not assertion.** Command output, the actual response, a screenshot, a
  console line. A criterion marked passed without evidence is an opinion.
- **Test with the specification's example data and its exact texts.** If the spec
  says the message reads *"Quantity must be greater than 0"*, then that is what you
  assert - not "an error appears".
- **Attack only this system, in a test environment, with test data.** Never against
  production, never against anybody else's system, and never with real personal
  data. You are testing your own product before it ships.
- **Never touch `.env.local`** or real secrets.
- **Lifecycle state and feature artifacts have different homes.** Read the board
  from the default checkout. Run and write the current `qa.md` and evidence manifest
  in the feature worktree. A feature branch's copy of the board is not current.
- **`qa.md` is one bounded current snapshot.** Before replacing it, copy the
  previous snapshot verbatim to
  `evidence/report-history/qa-<previous-tested-sha>-<run-id>-r<round>.md` in an
  unattended run. Outside the runner, use
  `qa-<previous-tested-sha>-manual-r<next-free-number>.md`. Treat the name as
  create-only: never overwrite an archive; advance the final number if the target
  already exists. Never append old rounds. The current report carries exactly one
  `kaitersberg-report: qa` marker and one `kaitersberg-subject-sha:` marker and is
  at most 128 KiB; link bounded evidence and archived rounds instead of embedding
  them. History stays inspectable without charging every later stage to read it.

## Full QA or targeted retest

- **Full** for the first tested SHA, when the previous report is not an ancestor,
  or when changes cross a migration, permission boundary, shared request path or
  another surface whose blast radius cannot be bounded.
- **Targeted retest** after `/build`: verify every previous blocking finding, run
  the ACs and edge/adversarial probes touched by `previous_sha..HEAD`, the affected
  automated suites, and one end-to-end smoke journey. Read from the spec only the
  touched ACs with their example data and texts, and from the previous `qa.md` the
  findings being verified - re-reading the whole spec every round is what makes a
  three-round loop cost three full QA passes. Reuse prior passing evidence
  for unchanged ACs only when the report names its source SHA. A reused result is
  evidence with provenance, not a claim that it was rerun. Escalate to full when the
  delta reveals a wider effect.

The full run establishes breadth; the targeted run establishes that the correction
works without charging every unchanged criterion again.

## Abort conditions
- The feature is not `In Review` in `features/INDEX.md` → say what state it is in.
- It is the foundation feature `PROJ-1` → there are no acceptance criteria to test
  against, so this skill does not run for it. Say so, point at the scaffold's
  `proof.md` and the `/review` that reads it, and at `/audit` for the repository-wide
  check later. Inventing criteria for a container definition is ceremony, and a
  verdict invented that way is worse than no verdict.
- `/review` returned `Changes required` and they were not fixed → testing a version
  that is already going back is wasted work.
- The application will not start → that is finding number one; report it and stop.

---

## Phase 0 - Set up

```
🧪 QA: PROJ-x [name]
```

1. Read `spec.md` - especially the acceptance criteria, the edge case table, the
   example data, the texts and formats table, the personal-data section, the
   security section, and the test plan with its levels.
2. Read `design.md` for the role differences and the protection limits with their
   numbers.
3. From `features/INDEX.md` in the default checkout, read only this feature's row;
   use the pick rule only when eligibility itself is in question. Then work in the
   feature's worktree and branch.
4. Start the application per `docs/local-dev.md` and run the seed command built by
   `PROJ-1`, which gives you **at least two tenants and one user per role**. Half of
   what follows is impossible with a single account. Add this feature's example data
   from the spec on top.
5. In full mode, reset to that known state before the automated suite and again
   before the browser walkthrough. In targeted mode, reset once and establish the
   fixtures needed by the affected paths. Record the commit, base URL, application version, database state,
   runner and browser versions, and every browser/viewport project under test.

## Phase 1 - The automated levels

First read `verification.json`. Reuse its lint, type and unaffected
unit/integration results from schema version 2 only when its full gate is green and
either HEAD equals `tested_sha`, or `git diff --name-only tested_sha..HEAD` contains
only the manifest and bounded evidence paths declared in
`allowed_post_test_paths`. A version 1 manifest with `head_sha` is reusable only
when that SHA equals HEAD; it cannot authorize an evidence-only descendant. Any
product, configuration or plan change makes the evidence stale. Run what QA
uniquely owns and what the selected mode requires: affected
automated tests, the project-owned browser suite or projects, plus the system,
migration, performance and adversarial checks below. If the manifest is missing,
stale or red, run the full local/CI commands. Record command, actual numbers,
first-run result, retries and artefact paths - not "green".

Retries diagnose instability; they do not erase it. A test that fails first and
passes only on retry is `flaky`, gets a finding and cannot support a production-
ready verdict until its cause is understood. Do not rerun a failed suite repeatedly
until it happens to pass. Preserve the first failure and its trace, screenshot,
console and failed-request evidence.

Then check the tests themselves, because a passing suite is only worth what it
asserts: pick the two or three criteria that matter most and **break the code on
purpose** - invert a condition, remove the tenant filter - and confirm the test
turns red. A test that stays green while the behaviour is broken is a defect in its
own right, and it belongs in the report.

Do those mutation probes in a disposable worktree or with a patch that is restored
in a trap, and prove the feature worktree clean afterwards. "Fix nothing" and
"break it deliberately" otherwise contradict each other when a process is killed.

## Phase 2 - Walk it in the browser

For every criterion the spec's test plan marked end-to-end or manual, and for the
journey step this feature belongs to, drive the real interface.

Invoke the `claude-in-chrome` skill before using any browser tool. Then:

- Open a new tab; do not hijack the user's tabs.
- Use the support matrix from `docs/app-shell.md`. Walk the primary browser at
  every required viewport the agentic tool can represent; the project-owned suite
  covers required browser engines. Record an unavailable walkthrough environment
  under *Not tested* rather than silently substituting another one.
- Walk the journey as the role would: the happy path first, then the same path with
  the wrong data.
- **Read the console and failed network requests** after each meaningful step
  (`read_console_messages` and the browser's network inspection) - a feature that
  works while throwing errors, unhandled rejections or unexpected failed requests
  is not passing.
- Check what only a human eye catches: the empty state before any data exists, the
  loading state, the error state, the exact wording against the spec's text table,
  number and date formats (a decimal comma is a defect if the spec says comma),
  the required viewport and reflow, accessible roles and names, and the keyboard
  path - reach the whole flow with the keyboard and watch where focus lands after
  saving and after an error.
- Capture a screenshot for every browser-tested criterion under
  `features/PROJ-x-<name>/evidence/`, named with its AC, browser and viewport. One
  artefact may support several criteria when the report links it from every row.
  In targeted mode, reuse an unchanged screenshot through the evidence manifest
  instead of copying it into another round.
  If the browser tool provides recording, also record the main flow; recording is
  supporting evidence, not a substitute for criterion-level results.
- Do not click anything that raises a browser dialog - it will freeze the session.

## Phase 3 - The migration, against data that already exists

Only when this feature brings one. A migration that has only ever run against an
empty database has been tested in the one case that never happens in production.

- Seed the previous state - the database as it is *before* this branch, with the
  seed set and this feature's example data - then run the migration the documented
  way and record how long it took.
- Check the rows that existed before: are the new columns filled the way the design
  said, or defaulted, or empty in a way that breaks the feature for old records?
- Walk one criterion that touches migrated data, not only newly created data.
- If `docs/architecture.md` requires reversibility, roll it back and forward again,
  and say what the round trip cost - a rollback that loses a column's data is a
  critical finding, not a note.

## Phase 4 - Edge cases

Work the spec's edge case table, one row at a time, and then the ones it forgot:

- The boundaries: zero, one, the maximum, one above the maximum, empty, the longest
  allowed string, the shortest.
- Nothing there: no records, no permission, no network, the dependency down.
- Twice: the same action submitted twice, two browser tabs, the back button after a
  save, a double click on the button.
- Wrong order: the steps done out of sequence, a stale page acting on a record that
  changed underneath it. Judge it against the concurrent-write rule in
  `docs/architecture.md`: a stale write that quietly wins where the architecture said
  it must be refused is a defect, not a curiosity - and two sessions changing the
  same record is the cheapest way to find it.
- Big and slow: the volume the spec named as its limit, and one order of magnitude
  of nonsense.
- **Against the budgets:** take the performance budgets from `docs/architecture.md`
  and measure this feature's paths at the volume the spec named - the list page, the
  write, the slowest job. Record the actual number next to the budget. Over budget
  is a finding with its measurement; no budget in the architecture is itself a
  finding, reported once. A number nobody measured is a promise nobody keeps.

Each one gets a row in the report whether it passed or not.

## Phase 5 - The adversarial pass

Now stop being a user. Everything here is done against your own test system with
test data, and every attempt is recorded whether it worked or not.

The probes are the rows of the adversarial table in
[report-template.md](report-template.md) - one list, kept where every report
already carries it, so the same nine probes are not maintained in two places.
Work them one at a time. Three are lost most easily: a hidden button is not an
access check, so bypass the interface; injected content does its damage where it
is displayed, printed or exported, not where it is typed; and a message or timing
that differs between "does not exist" and "not yours" is a directory of your
customers.

For each probe: what you tried, what happened, and what it means. A probe that
failed to break anything is a result worth writing down - it is what makes the
report trustworthy.

## Phase 6 - Report and verdict

Archive any previous current snapshot under the collision-free name above, then
replace `features/PROJ-x-<name>/qa.md` from
[report-template.md](report-template.md), and give the summary in the message.
Verify the two snapshot markers occur exactly once and the current file is no
larger than 128 KiB. **Everything the report leans on goes into the
same feature folder**, under `features/PROJ-x-<name>/evidence/`: screenshots,
recordings, captured responses, the output of a failing run. A report whose
evidence lives in a temporary directory is unreadable a week later, which is
exactly when somebody asks.

**Verdict - one of:**
- **Production ready** - every criterion passed, no defect above cosmetic, the
  adversarial pass found nothing that holds.
- **Ready with reservations** - passes, but with defects that are worth shipping
  around; each named, with what it costs to leave it.
- **Not production ready** - a criterion fails, or the adversarial pass found
  something real. Say which single finding decides it.

**Severity:**

| | Means |
|---|---|
| Critical | Data loss, a hole in the isolation, personal data where it must not be, anything letting a user act as another |
| Major | An acceptance criterion does not hold |
| Minor | Wrong text, wrong format, a rough state, an edge case behaving oddly |
| Cosmetic | Noticeable only if you are looking for it |

Any critical finding makes the verdict *Not production ready*, whatever else passed.

Say what you **could not** test, and why. A report that hides its gaps is worse
than a short one that names them.

Then:
- Not production ready → leave the owned feature on `In Review`; the current report
  and loop state send it to `/build`. `/review` sees the resulting delta in a fresh
  session, then this skill runs in targeted or full mode according to its blast radius.
- Otherwise → the feature stays `In Review` and goes to `/pr`.

In an unattended run, return exactly one structured outcome: `production_ready`,
`ready_with_reservations`, `not_production_ready`, `incomplete` when another QA
session must resume the checkpointed report, or `blocked` for a human decision.
Include the feature HEAD SHA.

## Checklist
- [ ] Application actually started; two tenants and one user per role created
- [ ] Full or targeted mode chosen from commit ancestry and blast radius, with source SHAs recorded
- [ ] Every AC has its own verdict with evidence
- [ ] Automated levels run, real numbers recorded
- [ ] Project-owned browser E2E suite run for every required project; commands, versions and artefacts recorded
- [ ] First-run failures preserved; retry-only passes reported as flaky findings
- [ ] Tests themselves probed by breaking the code on purpose
- [ ] Browser walkthrough done for the e2e and manual criteria, console and failed requests inspected
- [ ] Empty, loading, error states, exact texts, formats, required viewports, accessibility semantics and keyboard path checked
- [ ] Every edge case from the spec worked, plus boundaries, repetition and wrong order
- [ ] Migration run against a database that already had data; existing rows checked; reversibility exercised where required
- [ ] Feature paths measured against the architecture's performance budgets, actual numbers recorded
- [ ] Two concurrent sessions on one record judged against the architecture's stale-write rule
- [ ] Adversarial pass complete, every probe recorded whether it worked or not
- [ ] Tenant isolation attacked with a real foreign ID, through the API too
- [ ] Logs, audit records and error responses searched for personal data
- [ ] Severity assigned to every finding; any critical forces the verdict
- [ ] What could not be tested is named
- [ ] Report in the feature folder, evidence beside it under `evidence/`
- [ ] Board read from the default checkout and left on `In Review` throughout delivery feedback
- [ ] Previous QA snapshot archived verbatim under its run-and-round name without overwriting history; `qa.md` replaced, not appended
- [ ] Current QA report is at most 128 KiB and has exactly one report marker and one subject-SHA marker
- [ ] Nothing fixed, nothing committed beyond the report and its evidence
