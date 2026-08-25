---
name: architecture
description: Decide the house style of the whole product once - module boundaries, how a request runs, where tenant isolation is enforced, where business rules live, error handling, logging, background work, migrations and the test setup. Runs once after planning, so nineteen features do not invent nineteen answers. Writes no code.
argument-hint: "(no argument - runs once per product)"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: opus
---

# Architecture

## Role
`/plan-product` decided the stack in a table row. You decide how it is used. This
document exists so that the twelfth feature is built the same way as the first -
by a different agent, in a different week, without asking anybody.

Everything here is a decision that is expensive to change later and cheap to make
now, and every one of them would otherwise be made nineteen times.

## Hard rules
- **One decision per question, written once.** If a later feature needs a second
  answer, that is a change to this document, argued here - not a quiet exception in
  one module.
- **Show the shape, not the code.** A named folder layout, a request walking
  through its steps, an example of a name - yes. Working code - no.
- **Decide, do not survey.** "Either A or B, depending" is not an architecture. If
  it genuinely depends, name the rule that decides. Bringing alternatives to the
  two or three load-bearing decisions is discussion; bringing a menu of twelve is
  handing the work back.
- **Only what more than one feature needs.** Anything used by exactly one feature
  belongs in that feature's design, not here.

## Abort conditions
- No `docs/PRD.md` → nothing was planned. Point at `/plan-product`.
- `docs/architecture.md` exists → say so, and ask whether to revise a section
  rather than rewrite it. Rewriting it invalidates every design that cites it.

---

## Phase 0 - Read what is already decided

```
🏛 Architecture: <product>
```

- `docs/PRD.md` - the constraints row: stack, hosting, compliance, scale.
- `docs/data-model.md` - the entities, and the tenant isolation decision already
  taken there. You make it concrete; you do not overturn it.
- `docs/access.md` - the roles, so the permission check has something to check.
- `docs/app-shell.md` - routes and page patterns.
- `docs/local-dev.md` - the commands and the environment.
- Whatever exists in the repository already. In a repository with code, the
  architecture is largely written; your job is to read it out and name the
  deviations, not to declare a new one.

## Phase 1 - Propose one architecture, then let it be attacked

A list of questions is not a discussion; it makes the user do the architect's work.
Bring a proposal and defend it.

### 1. Derive the shape from the plan

Before asking anything, work out what the plan already forces. Most of an
architecture is dictated, not chosen:

| From the plan | Forces |
|---|---|
| The entities and their tenant key in `docs/data-model.md` | How isolation must work, and how much of it can be automatic |
| The roles and the permission matrix | Where the check has to sit to be checkable |
| The journeys and the app shell | How much of this is request-response and how much is not |
| Expected scale in the PRD | Whether anything here is a scaling problem yet - usually it is not |
| Compliance and hosting | What may leave the machine, and what must be recorded |
| Team size and the deadline | How much machinery this team can carry |

Write the resulting shape down as **one page**: the module layout, the path of a
request, where isolation is enforced, where rules live, how it is tested.

### 2. Name the load-bearing decisions

Two to four, no more. A load-bearing decision is one where the alternative would
produce a different product to work in - not a preference. For each:

- what you propose,
- the real alternative,
- **what each costs, in this product** - not in general,
- which one you recommend and why,
- how expensive it is to change later. That last one decides how hard to argue.

Everything else you decided already; list it briefly so the user can see it, but do
not open it. An architecture put up for a vote line by line never gets finished.

### 3. Put it up for attack

Present the one-page shape and the load-bearing decisions, and invite the
disagreement explicitly: *"Here is what I would build and why. These are the places
where I could be wrong."*

Say plainly **what would make this architecture the wrong one**: the assumptions it
rests on, taken from the PRD. Ten times the users. A second tenant type. An
offline client. Somebody buying the company and wanting it on their own servers.
The user knows things about the future that the plan does not contain, and the
premise is easier for them to check than the conclusion.

Use AskUserQuestion for the load-bearing decisions, recommendation first. For
everything else, take your own decision and move.

### 4. When the user disagrees

Take it. Then: if their choice costs something the plan will feel, say so once,
concretely - and build their choice. Record it under *Decisions* with the cost, so
the next reader knows it was chosen with open eyes rather than overlooked. Do not
argue the same point twice; a decision made and written down is made.

If it turns out mid-discussion that the plan itself is wrong - the data model
cannot carry what was decided, the roles do not work - **stop and fix the plan**.
An architecture built over a broken plan hides the break instead of showing it.

## Phase 2 - Write `docs/architecture.md`

Use [template.md](template.md). The sections that earn their place in nearly every
product:

| Section | The question it settles |
|---|---|
| **Module layout** | What a module is, what it contains, what it may not reach into, and what things are called |
| **Request path** | The steps every request takes, in order, and what each one is responsible for |
| **Tenant isolation** | Where exactly it is enforced, in one place, and how a new query inherits it without remembering to |
| **Permissions** | Where a role is checked, and why not in the interface |
| **Business rules** | Where they live, so they hold no matter which entry point calls them |
| **Validation** | Where untrusted input stops being untrusted |
| **Errors** | The kinds of failure, what each returns, what the user sees, and what is never in the message |
| **Logging and audit** | What is recorded, at which level, and what must never be in a log line |
| **Background work** | What runs outside a request, how it retries, what happens when it fails for good |
| **Files and secrets** | Where uploads go, where keys live, what never reaches the client |
| **Migrations** | The tool, the naming, whether they must be reversible, how they run in deployment |
| **Concurrent writes** | What happens when two people change the same record, and how a stale page is refused rather than silently winning |
| **Data conventions** | How time, decimals, rounding and units are stored and displayed - the answers nineteen features would otherwise each invent |
| **Retention and deletion** | What deleting actually does per entity - remove, anonymise, block - and how the retention the PRD promised is met |
| **Performance budgets** | The numbers from the PRD turned into rules a query, a page and a job must obey, and how a breach is noticed |
| **Dependencies** | Who may add one, what counts as justification, which licences are acceptable, and how they are updated |
| **Testing** | What is unit, integration and end-to-end here; which browser runner and commands are used; how the database is reset; how fixtures, selectors, waits, retries and failure artefacts work; what is never mocked |
| **Naming and structure** | The conventions a new file follows without asking |
| **Quality gate** | Which rules a machine enforces, at which threshold, and what the build gate runs |

Skip a section only by writing why it does not apply to this product.

**Every section gets a reason, not only a rule.** A rule without its reason is
followed until somebody finds it inconvenient; a rule with its reason survives.

### Module layout, in particular

Nineteen features will argue about where a piece of code goes, and they argue
better with one vocabulary than with nineteen. Fix these four words here and use
them in every design and every review:

- **Module** - anything with an interface and an implementation: a function, a
  class, a folder, a slice through the tiers. Deliberately not tied to a size.
- **Interface** - everything a caller must know to use it correctly. Not only the
  signature: the invariants, the order things must happen in, the ways it fails,
  the configuration it needs, what it costs to call.
- **Seam** - the place where that interface sits, and therefore the only place
  where behaviour can be swapped or observed without editing inside. Tests live at
  seams; a test that reaches past one is testing the implementation.
- **Deep and shallow** - a module is *deep* when a caller gets a lot of behaviour
  for the little they have to learn, *shallow* when its interface is nearly as
  complicated as what sits behind it. Deep is the goal, for two reasons worth
  naming: the caller gets leverage, and the maintainer gets one place to fix
  instead of one per caller.

Two rules settle most of the arguments and cost nothing to apply:

- **The deletion test.** Imagine the module gone. If complexity disappears with
  it, it was a pass-through and should not exist. If the same complexity reappears
  in every caller, it was earning its keep.
- **One implementation is a hypothetical seam, two is a real one.** Do not put an
  interface in front of something that does not vary. The interface with a single
  implementation is the abstraction this pipeline produces most easily, and the one
  `/review` is told to reject.

Then say which seams this product has **on purpose** - typically the database, the
outside services, the clock, and anything that gets a fake in tests - and that
everything else stays internal until something actually varies across it. That list
is what the testing section below relies on, and what stops nineteen features each
inventing their own place to swap things out.

### Performance budgets, in particular

The PRD promised numbers - response time, job duration, expected scale. Here they
become rules somebody can check, or they were decoration: the budget for a normal
page and a write, the budget for the slowest thing the product does, the query
rules that keep them (no unbounded list without pagination, no per-row query inside
a loop, which indexes exist because a journey needs them), and **how a breach is
noticed** - a test, a log threshold, or an honest "nobody notices yet, and that is
accepted until <event>". `/qa` measures against these numbers; without them it has
nothing to measure and the PRD's promise is never tested by anyone.

### The quality gate, in particular

Split every quality rule you write into the two kinds, because they are enforced in
different places and confusing them is why quality documents get ignored:

**Machine-enforced** - decided here, configured as real tooling by the foundation
feature, run by `/build` after every batch and by CI. A rule of this kind that
exists only as prose is not a rule, it is a wish. Name the tool, the setting and
the threshold:
- formatter and linter: which one, which rule set, which rules deliberately off
- type checking: how strict, and which escapes are forbidden outright
- **coverage: a floor that may not fall, not a target to reach.** A percentage
  target buys tests that assert nothing; a ratchet - this number may never go down -
  buys tests that arrive with the code. Say the current floor and that it moves only
  upward.
- limits: file length, function length, nesting, cyclomatic complexity - if you set
  them, set numbers
- boundaries: which module may import which, enforced by the linter, not by hope
- forbidden: the APIs, patterns and imports that must never appear, and the reason

**Where each of them runs.** The gate after a batch and in CI is the authority -
it cannot be skipped. A git hook is the earlier, cheaper copy of a *subset* of it,
and it is the only place a commit message can be checked at all, because nothing
downstream ever reads one. Decide three things and no more: which checks run in
`pre-commit` (fast ones on staged files only - a hook that runs the full test suite
gets bypassed by the second day), whether `commit-msg` enforces the commit format
from `CLAUDE.md`, and that hooks are versioned in the repository rather than left to
each developer to install. Say explicitly that `--no-verify` stays available and
that CI re-runs everything anyway - a hook is a fast correction, never the proof.

**Judgement** - decided here as a written expectation, enforced by `/review`,
because no tool can see it: is this abstraction earned, does this test assert the
behaviour or the mock, is this name the word from the data model, is this the
simplest thing that works.

Say plainly which is which. And decide the escape hatch now: a suppressed rule -
a lint disable, a type escape, a skipped test - **carries a reason on the same
line**, and `/review` treats one without a reason as a finding.

**Coverage honestly:** the spec-to-task-to-test chain already guarantees a test per
acceptance criterion, which is stronger than any percentage. The floor exists to
catch what has no criterion - helpers, error paths, the code somebody added on the
way. Treat a drop as a question, not a violation.

## Phase 3 - Anchor it

1. Add `docs/architecture.md` to the project's `CLAUDE.md` imports, so every
   session gets it without being told. **A repository worked from more than one
   harness carries more than one context file in its root** - update every one of
   them, not only the one this session reads. They are read by different sessions,
   nobody diffs them, and the one you skipped keeps telling its readers that the
   architecture does not exist yet.
2. **Hand the machine-enforced half to `/scaffold`.** The linter configuration, the
   type settings, the coverage floor and the boundary rules are files somebody has
   to write; that is `PROJ-1`, wave 1, and `/scaffold` builds it directly from this
   document. Every threshold you leave vague here becomes a guess there.
3. Replace any `decided by /architecture` browser E2E marker in
   `docs/local-dev.md` with the exact local and CI commands chosen here.
4. Note in `docs/PRD.md`'s constraints table that the architecture document now
   carries the detail.
5. Tell the user which of the decisions are the ones worth arguing about now,
   because they are the expensive ones later:

```
## Architecture decided

**Expensive to change later:** <the three or four that matter>
**Left open on purpose:** <what waits for a real case, and which one>

Next: `/scaffold`.
```

6. Commit: `docs: Add architecture`

## Checklist
- [ ] The shape derived from the plan before any question was asked
- [ ] A one-page proposal put to the user, not a list of questions
- [ ] Two to four load-bearing decisions named, each with its alternative and both costs
- [ ] What would make this architecture wrong stated, from the PRD's assumptions
- [ ] Disagreement taken, its cost stated once, then built as chosen and recorded
- [ ] Existing code read before anything was declared
- [ ] Module vocabulary fixed - module, interface, seam, deep and shallow - with the deletion test and the two-implementations rule
- [ ] The seams this product has on purpose listed, and everything else declared internal
- [ ] Tenant isolation decided in exactly one place, and how new queries inherit it
- [ ] Permission check located where the action happens, with the reason
- [ ] Error, logging and audit rules include what must never appear in them
- [ ] Migration and testing conventions concrete enough to follow without asking
- [ ] Concurrent writes decided: stale writes refused or merged, in one mechanism
- [ ] Time, decimal, rounding and unit conventions fixed once, with the storage and display rule
- [ ] Deletion decided per entity - removed, anonymised or blocked - and retention met by a named mechanism
- [ ] Performance budgets carry the PRD's numbers, the query rules that keep them, and how a breach is noticed
- [ ] Dependency policy decided: who adds, what justifies, which licences, how they are updated
- [ ] Browser E2E runner, local and CI commands, supported projects, state isolation, locator policy, waits, retries and failure artefacts decided
- [ ] Visual regression explicitly enabled with an approved baseline, or explicitly not used
- [ ] Quality rules split into machine-enforced and judgement, and labelled as such
- [ ] Every machine-enforced rule names a tool, a setting and a number
- [ ] Git hooks decided: which checks run pre-commit, whether commit-msg is enforced, and that the gate stays the authority
- [ ] Coverage set as a floor that may not fall, with the current number
- [ ] The escape hatch decided: suppressions carry a reason on the line
- [ ] Every rule carries its reason
- [ ] Nothing in here is needed by only one feature
- [ ] Added to `CLAUDE.md` imports - and to every other harness context file the repository root carries
- [ ] Browser E2E commands written back to `docs/local-dev.md`
- [ ] No code
