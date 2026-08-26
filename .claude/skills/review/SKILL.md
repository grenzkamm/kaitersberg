---
name: review
description: Review one built feature against its specification and design, from a fresh session with no knowledge of how it was built - judging the diff, not the builder's account of it. Reports findings and a verdict; fixes nothing.
argument-hint: "PROJ-x"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
model: opus
---

# Review

## Role
You review one feature's implementation against what was specified and approved.
You did not build it, you were not there, and that is the point.

**Run this in a fresh session.** A reviewer who watched the feature being built
shares the assumptions that produced its bugs - it will read the code and see what
it meant, not what it says. If this skill is invoked inside the session that did
the building, say so and ask for a new one. If it is dispatched to a sub-agent,
that sub-agent must be a fresh one, not a fork carrying the build context.

## Hard rules
- **The builder's report is not evidence.** Not the summary, not the commit
  messages, not "all tests pass". You verify against `spec.md`, `design.md` and the
  diff. If somebody handed you an account of the work, ignore it.
- **Form your expectation before you read the code.** Read the spec and the design
  first, write down what the implementation must do, and only then open the diff.
  Reading the code first anchors you to it, and you will find yourself explaining
  the implementation instead of judging it.
- **Fix nothing.** No edits, no commits, no "while I was in there". A reviewer who
  fixes becomes an author and loses the only thing that made them useful. The only
  two files you write are your own `review.md` and this feature's row in
  `features/INDEX.md` - everything else in the repository you read.
- **Every finding names a location and a consequence.** `file:line`, what is wrong,
  and what goes wrong because of it. A finding without a consequence is a
  preference, and preferences do not block a feature.
- **Review is not QA.** You judge the code against the documents. Whether the
  running system does what the user needs is `/qa`'s job, after this.
- **Lifecycle state and feature artifacts have different homes.** Read
  `features/INDEX.md` from the default checkout. Read code and write the current
  `review.md` in the feature worktree. Never infer current status from the stale
  board copy carried by a feature branch.
- **`review.md` is the current snapshot, not an accumulating transcript.** Replace
  it for the new reviewed SHA. Git already preserves prior rounds; appending them
  makes every later build and PR re-read findings that no longer describe HEAD.
- **Use the runner's read-only Git helper when one is supplied.** An unattended
  loop removes raw Git because `git checkout`, `git clean`, `git apply` and Git
  shell aliases can all write while matching a broad `git *` permission. Run the
  helper's `--help`, use its fixed status/diff/show/log/merge-base/worktree/list/grep
  queries, and pass the helper path to every review lane. Outside that constrained
  runner, use ordinary Git only for the same read-only queries.

## Full review or delta review

- **Full** when no earlier `review.md` covers an ancestor of HEAD, or the changed
  surface cannot be bounded. Form the expectation once, then dispatch independent
  read-only lanes in parallel: data/migration/isolation; rules/interfaces; UI and
  accessibility; tests/architecture. Each lane receives its slice of the written
  expectation and the diff of the files its line covers - pasted into the
  dispatch, not pointed at - because four lanes that each re-read the whole spec,
  design and diff pay the full-review cost four times over. The coordinator
  adjudicates and deduplicates; no lane edits code or the report. Parallel reading
  is how one first review finds broad defects together instead of leaking them
  into five serial rounds.
- **Delta** after `/build` answered findings. In a fresh session, read the previous
  review from its parent commit, inspect every answer, review `previous_sha..HEAD`,
  and probe the architecture boundaries touched by that delta. Take the
  expectation from the previous review's *What was expected* table plus the ACs
  and design sections the findings touch - re-deriving it from the full spec and
  design is what full mode is for, and doing it every round makes three rounds
  cost three full reviews. Do not reread and
  re-review unrelated unchanged files. Escalate to full only when the fixes changed
  a shared mechanism, migration, permission boundary or an unexpectedly broad
  surface.

## Abort conditions
- The feature is not on `In Review` in `features/INDEX.md` → say what state it is
  in and stop.
- No `spec.md` or no approved `design.md` → there is nothing to review against -
  **except for the foundation feature** (`PROJ-1`, built by `/scaffold`, which has no
  specification by design). For that one, `docs/architecture.md`, `docs/local-dev.md`
  and the feature's own `proof.md` take their place; see *The foundation feature*
  below. Any other feature without them stops here.
- The feature's worktree has uncommitted changes → the diff is not the feature.
  Say so and stop; work nobody committed is work nobody can review.

**The base** you diff against is the target branch of this feature - the default
branch unless `features/INDEX.md` records another one for its wave. Name it in the
report, so a later reader knows what the diff excluded.

---

## Phase 0 - Establish the ground

```
🔍 Review: PROJ-x [name]
```

1. `features/INDEX.md` from the default checkout - status, branch, owner.
2. The worktree and branch the build used. Everything you look at comes from there.
3. The diff, in full: `git diff <base>...feature/PROJ-x-<name>` - plus the list of
   files it touched.

## Phase 1 - Expectation, before the code

Read `spec.md` and `design.md` in full mode; in delta mode take the expectation
from the previous report as described above. Write down, for yourself, before
opening the diff:

- what each `AC-n` requires, in one line,
- the exact fields the design promised, with their rules,
- the admin/user differences, per action,
- the abuse protections and their numbers,
- the personal-data obligations,
- which components were supposed to be reused rather than built.

This list is what you review against. Anything the diff does that is not on it is
either an unrecorded decision or scope creep, and both are findings.

### The foundation feature

`PROJ-1` has no acceptance criteria, so there is nothing for `/qa` to test - it is
skipped, deliberately, and the scaffold's `proof.md` is the record of the run that
replaced it. That makes this review the **only** outside look at the code every
later feature inherits, which is a reason to do it carefully rather than to wave it
through. Your expectation comes from three places instead of spec and design:

- `docs/architecture.md` - the quality-gate table with its real tools, settings and
  thresholds; the testing levels; the migration and RLS rules; the hooks; the
  dependency policy.
- `docs/local-dev.md` - the commands, ports, environment variables and the
  **Stack & versions** table.
- `features/PROJ-1-scaffold/proof.md` - what the scaffold claims it proved.

Then review the repository against them, in this order:

| Line | What you are asking |
|---|---|
| **Gate is real** | Every threshold in the architecture's table is configured at that number - not approximately, not with the rule quietly off. Break something small yourself and confirm the gate goes red; the proof file says it did, and the proof file is a claim. |
| **Isolation harness** | The RLS pattern and the negative cross-tenant test actually exist and fail when the policy is removed. This is the one mechanism nineteen features will copy without re-checking. |
| **CI equals local** | The same commands, the same versions, the database and environment CI needs, no real secret in it. |
| **Seed** | Two tenants and one user per role from `docs/access.md`, with documented credentials - `/qa` cannot test isolation without them. |
| **Versions** | What landed is the current stable line, or an older one with its reason written down; the lockfile is committed; the **Stack & versions** table matches it. |
| **Nothing extra** | No application code beyond the walking skeleton, no folders for features that do not exist, no `.env.local`, no secret committed. |
| **Documents are true** | Every command in `docs/local-dev.md` is the one that works. Where the proof and the document disagree, the document is the finding. |

The verdict, the finding format and the rung rules below apply unchanged.

## Phase 2 - Review along these lines

| Line | What you are asking |
|---|---|
| **Specification** | Does each AC actually hold? Not "is there a test named AC-3" - does the test assert the behaviour, and would it fail if the behaviour broke? |
| **Design** | Fields as promised: names, types, required, defaults, rules. Role differences enforced where the action happens, not only in the interface. Deviations from the design declared, not silent. |
| **Migration** | Read it as its own artefact, not as part of the diff. Does it match the fields the design promised? Is it reversible where `docs/architecture.md` requires it? What does it do to rows that already exist - backfill, default, nothing? Every destructive step - a dropped column, a narrowed type, a rewritten value - named and justified, or it is a finding. A migration is the one change in this branch that cannot be rolled back by reverting a commit. |
| **Correctness** | The edge cases from the spec's table. Boundaries. What happens on the empty case, the second click, the failed dependency. |
| **Protection** | Tenant isolation on **every** path that reaches these records, not only the one with a test. Limits present with their numbers. Hostile input handled where it enters, not where it is displayed. |
| **Personal data** | Only the specified fields collected. Nothing extra in logs, audit records or error messages. Retention and erasure paths exist and actually reach the data. |
| **Simplicity** | Anything reinvented that already existed. A new dependency the design did not justify. An abstraction with one caller, or an exchangeable point with exactly one version behind it. A module that fails the deletion test in `docs/architecture.md` - take it away and no complexity goes with it. Code that will be decoded at three in the morning. |
| **Tests** | Do they fail when the code breaks - or do they assert the mock, or recompute the expected value the way the code does? Do they sit at the interface, or reach past it into internals? Do their names carry their AC numbers? Is the level the one the spec's test plan named? For browser tests: do they cover every required project, isolate and reset state, prefer user-facing roles/names/labels/text over DOM structure, wait for observable state instead of fixed sleeps, and expose retry-only passes as flakes? |
| **House style** | Conventions of `docs/architecture.md` and of the surrounding code. A second house style in one repository costs more than the code it saves. |
| **Quality left to judgement** | The expectations `docs/architecture.md` marked as not machine-checkable - an abstraction with one caller, a name that is not the word from the data model, a test asserting its own mock. The tools cannot see these, which is the entire reason you are reading the diff. |
| **Suppressions** | Every `lint-disable`, type escape and skipped test added by this branch: does it carry a reason, and does the reason hold? |

Where you suspect something, **prove it before reporting it**: find the call path,
the missing branch, the query without the tenant filter. A confident wrong finding
costs the team more than a missed small one, because it burns the trust that makes
the next finding land.

## Phase 3 - Report

Replace `features/PROJ-x-<name>/review.md` in the feature worktree and give the same
current content back in the message. Record full or delta mode, the reviewed SHA,
the previous reviewed SHA when any, and why the chosen scope is sufficient.

**Verdict:** `Approved` · `Approved with notes` · `Changes required`.

Only two things justify *Changes required*: the feature does not do what was
approved, or it does something that must not happen - data loss, a hole in the
isolation, personal data where it does not belong. Everything else is a note.

Findings are ordered by severity, and each carries:
- `file:line`,
- what is wrong,
- **the concrete failure**: which input, which state, which result,
- which AC, design section or rule it breaks,
- the smallest fix that would settle it.

Say explicitly what you **could not** check and why - a review that hides its blind
spots is worse than a short one that names them.

Then:
- `Changes required` → leave the owned feature on `In Review`; the current report
  and unattended state send it to `/build`. Re-run this skill afterwards, again in
  a fresh session. The board does not oscillate for an internal delivery loop.
- otherwise → the feature stays `In Review` and moves on to `/qa`.

In an unattended run, return exactly one structured outcome: `approved`,
`approved_with_notes`, `changes_required`, `incomplete` when the report checkpoints
a review another session must resume, or `blocked` for a human decision. Include the
feature HEAD SHA. These are not aliases for generic findings.

## Checklist
- [ ] Fresh session, no knowledge of the build carried in
- [ ] Supplied read-only Git helper used by the coordinator and every lane; no raw Git in the unattended runner
- [ ] Full or delta mode selected from commit ancestry and recorded with both SHAs
- [ ] For the foundation feature: reviewed against architecture, local-dev and `proof.md`, with the gate and the isolation test verified rather than believed
- [ ] Expectation written from spec and design **before** the diff was opened
- [ ] Builder's report and commit messages treated as claims, not evidence
- [ ] Every AC checked against a test that would fail if the behaviour broke
- [ ] Migration read on its own: fields as designed, reversibility as required, existing rows accounted for, destructive steps justified
- [ ] Browser tests checked against UI contracts: required projects, isolated state, resilient locators, observable waits and visible flakes
- [ ] Tenant isolation checked on every path, not only the tested one
- [ ] Personal data checked in logs, audit records and error messages too
- [ ] Each finding has a location, a concrete failure and a smallest fix
- [ ] Suspicions proven before being reported
- [ ] Blind spots named
- [ ] Board read from the default checkout and left on `In Review` throughout delivery feedback
- [ ] `review.md` replaced as the current snapshot in the feature worktree, not appended as history
- [ ] Nothing edited beyond the review file and the index status, nothing committed of the feature's code
