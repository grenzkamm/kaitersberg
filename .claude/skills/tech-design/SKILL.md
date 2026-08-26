---
name: tech-design
description: Translate one feature specification into a technical design that a non-developer can read and sign off - what gets built, what changes for each role, the exact fields the feature stores, the admin/user difference, and the effect on what already exists. No code, no SQL.
argument-hint: "PROJ-x (optional - takes the next feature with a spec but no design)"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: opus
---

# Tech Design

## Role
You translate one specification into a design document with two jobs at once:

1. **A non-developer reads it and approves it.** They must be able to tell, without
   asking anybody, what will exist afterwards, what it changes for their people,
   what gets stored about whom, and what an administrator can do that an ordinary
   user cannot.
2. **A developer or an agent builds from it without inventing anything.** Every
   field is named with its type, its rule and whether it is required. Every role
   difference is stated per action.

Those two are not in conflict. Precision is not the same as jargon. A table saying
*"Quantity · decimal number with 3 places · required · greater than 0"* is exact
enough to build from and plain enough to approve.

## Hard rules
- **No code, no SQL, no framework names in the body.** Not `VARCHAR(200)`, not
  `POST /api/x`, not "we use a repository pattern". Those belong to the
  implementation and would only make the reader skip the page.
- **But no vagueness either.** "The relevant data is stored" is a failed design.
  Name the fields. A section that cannot be made concrete is an open decision, and
  belongs under *To decide*, not in prose.
- **Every acceptance criterion from the spec must be covered.** The coverage table
  is what proves it. An AC nobody designed for is an AC nobody will build.
- **Admin and ordinary user are always separated**, per action, even when the
  answer is "no difference" - write that down rather than leaving it open.
- Write the document in the language of the specification.

## Abort conditions
- No `spec.md` for this feature → the design has nothing to translate. Point at
  `/write-spec`.
- The spec has open questions that would change the data or the roles → list them
  and ask whether to decide them here or to settle them in the spec first.
- `design.md` already exists → open it and ask whether to revise it.
- No `docs/architecture.md` → this skill leans on its deletion test, its
  exchangeable-point rule, its dependency policy and its migration rules. Say so and
  point at `/architecture` rather than inventing a second house style here.

---

## Phase 0 - Pick the feature

```
📐 Design: PROJ-x [name]
```

With an argument, take that ID. Without, take the first feature whose folder has a
`spec.md` but no `design.md`. If several qualify, ask which.

## Phase 1 - Read

- `features/PROJ-x-<name>/spec.md` - the whole thing, including the tables most
  people skip: example data, texts, side effects, personal data, security.
- `docs/data-model.md` - the entities that already exist and what they are called.
- `docs/access.md` - the roles and the permission matrix.
- `docs/app-shell.md` - the routes and page patterns already decided.
- `docs/architecture.md` - the house answers this design must apply rather than
  re-decide: concurrent writes, time/decimal/rounding/unit conventions, retention
  and deletion, migration rules including whether reversibility is required, the
  performance budgets, and the dependency policy this design's dependency section
  is measured against.
- The `design.md` of neighbouring features that share an entity, a route or a
  component with this spec - so the same problem is not solved two different ways.
  Only those: reading every design on the board grows linearly with the product
  and adds nothing for features this one never touches.
- What is already built: `git ls-files` for the modules and screens this touches.

## Phase 2 - Decide the data

This is the part the approval hangs on, so do it first and do it fully.

For every entity the feature writes, list **every field**, using this vocabulary
so the reader and the builder read it the same way:

| Type | Means |
|---|---|
| Text, short | One line, with a maximum length |
| Text, long | Several lines, free text |
| Whole number | No decimals |
| Decimal number (n places) | Say how many places - money and quantities differ |
| Amount of money | Currency named |
| Date / Date and time | Say which, and in whose time zone |
| Yes / No | Say what the default is |
| One of a list | List the values and what each means |
| Reference to <entity> | Say what happens when the referenced record disappears |
| File | Say which formats and the size limit |

Per field: **name · meaning · type · required? · default · rule · personal data? ·
new or already there**.

Three things are as important as the fields themselves:
- **What is deliberately not stored**, and why. This is where over-collection dies.
- **Status values and what each one means** in the business, not in the code.
- **Which of this is new to `docs/data-model.md`** - a new field is a change to the
  plan, and the plan gets corrected in Phase 6, not silently diverged from.

## Phase 3 - Decide the roles

One table, one row per action in this feature, one column per role. The
**administrator and the ordinary user always get their own columns**, even in a
product with more roles.

For every difference, one line of reason. "Only the administrator may delete,
because a deleted record takes its history with it" is a reason. "Admin only" is
not.

Rules that repeat across features - a user may only see their own records, an
administrator sees the whole tenant - are stated here too, in this feature's terms.
The reader approves this document, not `docs/access.md`.

## Phase 4 - Sections the feature earns

Beyond data and roles, a design carries only the sections this feature actually
needs. Fill one, or delete it with a one-line reason - a heading with nothing
under it reads as "nobody looked".

**Always:** overview · what changes per role · roles and rights · data ·
behaviour · effect on what exists · AC coverage · to decide · approval.

**When the feature has one:**

- **Concurrent behaviour** - mandatory whenever the feature writes mutable data.
  Name the actions that can collide, apply the concurrency mechanism already fixed
  in `docs/architecture.md`, say what a stale or duplicate actor sees, and state
  what the data looks like afterwards. Do not re-decide the house mechanism here;
  an exception is a technical decision and must name the rule it departs from.
- **Migration** - for every feature that changes the shape of stored data. What
  runs, in order; which existing rows get which value and from where; **every
  destructive step named** - a dropped column, a narrowed type, a rewritten value -
  with why it is safe; and whether it is reversible, against what
  `docs/architecture.md` requires. `/review` reads the migration against this
  section and `/qa` runs it against a database that already has data: an
  unwritten backfill is a silent decision, and a destructive step nobody named is
  the one that gets noticed in production.
- **Component structure** - the parts of the interface as a tree, and next to each
  one whether it **already exists and is reused**, is extended, or is new. Take the
  existing ones from `docs/design-system.md` and from what is built
  (`git ls-files`). A part marked "new" that already exists two features over is
  the single most common waste in this pipeline, and this is where it is caught.
  For everything still marked new, ask the deletion question: *if this part did not
  exist, would its work disappear - or would the same work reappear in three
  places?* If it would disappear, the part is a pass-through and the design is
  shorter without it.
- **Pages and routes** - route, page pattern from the app shell, what is on it.
  A route that is not in `docs/app-shell.md` gets added there in Phase 6.
- **Abuse protection** - for anything a user can reach. Not the threat list from
  the spec repeated, but where the defence sits: which check happens before which
  step, what the limits are in numbers, what an abuser sees when they hit one, and
  what gets recorded. Tenant isolation is named here even when it is "the same rule
  as everywhere" - the approver reads this document, not the architecture.
- **Configuration** - every setting this feature introduces: name, what it does,
  default, who may change it, and whether it is per tenant or for the whole
  installation. A value that will never change is not configuration; hard-code it
  and say so.
- **Environment variables** - name, purpose, example value, and **server-side
  only?** with the reason. Every new variable is added to `.env.local.example` and
  `docs/local-dev.md` in Phase 6, or it will be missing on the first deploy.
- **Secrets and keys** - whenever the feature signs, hashes, pseudonymises or
  encrypts anything, or reaches an outside service with a credential. For each
  one: what it protects, **where its value comes from**, what it is deliberately
  separate from, whether it may rotate and what happens to values already stored
  when it does. An unnamed key source is the gap that gets filled during the build
  with whatever looks reasonable - an unkeyed hash where the design meant a keyed
  one still reads as irreversible, so it passes review and is still not what was
  approved. Ask this before the approval, not after, and never write
  `.env.local`: the repository gets example values only.
- **Dependencies** - every package this feature would add: what it does, what it
  replaces, and why the standard library, the platform, or something already
  installed does not do it. A dependency without that third column does not get
  approved. The bar and the acceptable licences are the dependency policy in
  `docs/architecture.md`; apply it, do not invent a second one, and name the licence
  whenever it is anything but the usual permissive ones. Name the package, not a
  version: the current stable one is resolved when it is installed, the same way
  `/scaffold` did it, and a version out of memory is a version that was already old
  when it was written down.
- **Technical decisions** - the choices worth recording: what was decided, what the
  alternatives were, why this one, and what it costs later. Two or three per
  feature at most; every decision written down is one nobody has to re-derive, and
  ten is a sign the feature was cut too large. Where a decision is about making
  something exchangeable later - one payment provider, one export format, one
  notification channel - apply the rule `docs/architecture.md` fixed for it:
  **build the exchangeable point only once a second version actually exists.** One
  version behind an exchangeable point is machinery nobody uses, and it is the
  waste this pipeline produces most easily after the duplicated component.
- **Outside contact** - external services, what leaves the system, what happens
  when they are unreachable.
- **Limits and assumptions** - with numbers.

## Phase 4b - Describe the behaviour in plain steps

- **What changes for whom**: one short paragraph per role from the spec.
- **Rules that always hold**: the invariants of this feature - what must be true
  before and after every action, regardless of who triggered it.
- **The flow**: the main scenario as numbered steps, in the words of the business.
  "The user picks a customer, the system offers the last three recipes of that
  customer, the user changes the amounts, the system recalculates the total."
- **Screens**: which route, which page pattern from the app shell, what appears on
  it, and what is new versus reused.
- **Outside contact**: every external service touched, what leaves the system, and
  what happens when it is unreachable.
- **Effect on what exists**: which records already in the database are affected,
  what happens to them, whether anything becomes invalid, and whether the change
  can be undone.
- **Limits and assumptions**: what this design assumes to be true, and where it
  will stop working - a number, not a feeling.

## Phase 5 - Coverage and open decisions

- **Coverage table**: every `AC-n` from the spec, and where in this design it is
  answered. An AC with no row is a gap; close it or say why it is out.
- **To decide**: everything you could not settle from the documents. Each with the
  options, your recommendation, and what it costs to be wrong. These are what the
  approver actually decides - the rest they only confirm.

Ask the user about anything under *To decide* that blocks the design itself
(AskUserQuestion, recommendation first). Anything that only affects the
implementation stays written down and moves on.

## Phase 6 - Write, correct the plan, hand off

1. Write `features/PROJ-x-<name>/design.md` from [template.md](template.md).
2. If the design went beyond the plan, correct the plan and list every correction
   in the design's own section for it. The test is the same one every skill here
   uses: **would somebody who reads only the plan now believe something false?** A design that diverges silently makes the
   plan a lie.
   - new fields or entities → `docs/data-model.md`
   - new role rules or limits → `docs/access.md`
   - new routes → the route map in `docs/app-shell.md`
   - new components → `docs/design-system.md`
   - new environment variables → `docs/local-dev.md` and `.env.local.example`
3. `features/INDEX.md`: leave the status at `Spec` while the design is a draft.
   **On approval, set it to `Designed`** - that is what tells `/tasks` it may start
   and what tells the board this feature has been signed off.
4. Present for approval:

```
## PROJ-x - [name], technical design

**Stored:** N fields on <entity>, of which M are new - <the personal ones named>
**Admin may, user may not:** <the differences in one line each>
**Changes for existing data:** <one line, or "none">
**To decide before this is built:** <the open points, or "none">

Approve, or say what should change.

Next after approval: `/tasks PROJ-x`.
```

5. On approval, fill the approval block in the document - who, when, with which
   conditions - and commit: `docs(PROJ-x): Add technical design for [name]`.

## Checklist
- [ ] Spec read in full, including its tables
- [ ] Every field named with type, required, default, rule and personal-data flag
- [ ] What is deliberately not stored is written down
- [ ] Status values explained in business terms
- [ ] Role table has its own admin and ordinary-user columns, every cell filled
- [ ] Every role difference carries a reason
- [ ] Flow written as numbered steps a non-developer can follow
- [ ] Every feature that writes mutable data has explicit concurrent behaviour: collision, house mechanism, actor-visible outcome and resulting data
- [ ] Effect on existing data answered, including whether it is reversible
- [ ] Migration described where data changes shape: order, backfill, every destructive step, reversibility against the architecture's rule
- [ ] House answers applied from `docs/architecture.md` - concurrency, formats, retention, dependency bar - not re-decided here
- [ ] Components marked as reused, extended or new - reuse checked against what exists
- [ ] Every part still marked new survives the deletion question
- [ ] Nothing made exchangeable that has exactly one version today
- [ ] Abuse protection designed with numbers, not intentions, wherever users can reach it
- [ ] Every new setting, environment variable and dependency named and justified
- [ ] Everything signed, hashed, pseudonymised or encrypted names its key, where the value comes from, and what rotation does to stored values
- [ ] Technical decisions recorded with their alternatives and their later cost
- [ ] Sections the feature does not need are deleted with a reason, not left empty
- [ ] Every AC from the spec appears in the coverage table
- [ ] Open decisions carry options, a recommendation and the cost of being wrong
- [ ] Plan documents corrected where the design went beyond them
- [ ] No code, no SQL, no framework names
- [ ] Approval block filled only after the user actually approved
- [ ] `features/INDEX.md` set to `Designed` on approval, not before
