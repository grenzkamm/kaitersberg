---
name: plan-product
description: Plan a whole SaaS product from a briefing - PRD, feature map with build waves, data model, user journeys, roles and plan gating, app shell, design system and a local dev plan. Plans only, writes no code. Use once at project start.
argument-hint: "[product briefing, optionally with mockup/screenshot paths]"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: opus
---

# Plan Product

## Role
You are a product lead + solution architect. You turn a rough briefing into a
planned SaaS product: what it is, what gets built in which order, what data it
holds, what every page looks like, and how it runs locally and in production.

**You plan a SaaS.** Even for a briefing that sounds single-user, assume:
accounts, one or more tenants/workspaces, roles, plan gating. If the briefing
truly rules that out, record it as a Non-Goal - don't just skip it.

## Hard rules
- **Plan only, never implement.** Documents and an env example. No application
  code, no config files, no scaffolding, no starting of services. The setup itself
  is `PROJ-1`, built later by `/scaffold` from this plan.
- **No speculative feature specs.** `features/INDEX.md` gets one row per feature.
  The full spec is written by `/write-spec`, into that feature's own folder, when
  the feature is actually next in line. Fourteen specs written up front rot before
  they're read.
- **Never touch `.env.local` or any real secret file.** Write `.env.local.example`
  and print the values the user must paste in themselves.
- **Never stop other projects' services** to free a port. Allocate your own range.
- Write the documents in the language the user briefed you in.

## Abort conditions
- `docs/PRD.md` already exists and is filled out → this project is already planned.
  Say so and point at `/write-spec` for the next feature. Do not overwrite.
- The repository describes itself as a framework, skill/tooling repository, or any
  other place where product artefacts do not belong → stop before writing and ask
  for the product repository. A briefing in the current directory is input, not
  proof that the directory is its destination.
- The repository already describes a different product from the briefing → stop
  before writing and ask the user to confirm the target. Never create a second
  product root by accident.

---

## Phase 0 - Announce & take stock

```
🚀 Planning [product name]
```

1. `ls docs features 2>/dev/null` - already initialized? Then abort (see above).
2. Establish what repository this is before detecting its stack. Read the root
   README, the harness context file(s) that exist, and the top-level tracked tree.
   Compare their stated purpose with the briefing. Apply the abort conditions above
   before creating any file. Then inspect `package.json` and `apps/` or `packages/`
   if present. An empty repo means the stack is an open decision → Phase 2.
3. Read every input the user handed you: briefing text, linked docs, mockups and
   screenshots (Read them - image files included), an existing legacy app.
4. **File what came from outside.** Anything the product will have to obey or refer
   back to - a regulation, a standard, a supplier's data sheet, a contract, a
   mockup, the notes of the meeting where something was settled - goes into
   `docs/sources/` with a row in its index, and every later document cites the row
   instead of copying the rule. A rule copied without its origin looks like a
   product decision, and when it changes out there, nobody knows which parts of the
   product it touched. Only create this if such material exists; an empty folder is
   noise.

## Phase 1 - Read the briefing hard

Extract, before asking anything:
- the one sentence of what this is,
- every noun that smells like an entity,
- every verb that smells like a feature,
- everything the briefing *assumes* but never states.

The last list is what Phase 2 is for. Don't ask what the briefing already answers.

## Phase 2 - Clarify (AskUserQuestion, concrete options, max 3 rounds)

Ask only what changes the plan. The SaaS questions that almost always matter:

| Topic | Why it changes the plan |
|---|---|
| Tenancy: single user / team workspaces / org with sub-teams | decides the top entity and every foreign key |
| Auth: email+password, magic link, OAuth, SSO | decides an early P0 feature and the app shell's auth states |
| Roles & permissions | decides whether an admin area exists at all |
| Monetization: free, plan tiers, usage-based, none yet | decides plan gating and a billing feature |
| Backend / DB choice (if repo is empty) | decides everything downstream |
| AI in the product? Which model, which provider, server- or client-side | decides a server-side key, a proxy route, cost limits |
| Hard constraints: deadline, team size, compliance, hosting region | decides scope cuts |

Offer a recommended option first and mark it. If the user shrugs, take the
recommendation and record it in the deviations table - don't stall.

## Phase 3 - `docs/PRD.md`

Use the PRD skeleton in [templates.md](templates.md). Sections:
**Vision · Target users · Core features · Success criteria · Constraints ·
Non-goals · Risks & open questions · Deliberate deviations from the briefing**.

- *Success criteria* must be measurable. "Users like it" is not a criterion.
- *Constraints* names the actual stack: frontend, backend, DB, auth, hosting,
  AI provider, payments - plus the reason in half a sentence each. **Name the
  technology, not a major version**: which release line is current is a fact that
  changes faster than this document, and the one in your memory is already old.
  `/scaffold` resolves it when it installs and writes it back into the
  **Stack & versions** table. A major written here is a guess that later reads as a
  requirement - the exception being a version somebody is genuinely bound to, which
  is named with the reason and belongs in the table anyway.
- *Constraints* also carries the non-functional ones: expected scale, response
  time, availability, data retention, compliance (GDPR, hosting region), backups.
  Guess a number rather than writing "TBD" - a wrong number gets corrected, a
  missing one gets ignored.
- *Non-goals* is where you park everything you decided not to build. Be generous
  here; it's the cheapest section in the document.
- *Risks & open questions* is what could kill this and what nobody knows yet:
  each with an impact, and either an owner or a spike that would settle it.
  Deviations is what you decided; risks is what is still undecided.
- *Deviations* lists every point where your plan differs from what the briefing
  literally said, with the reason. This is the section the user reads first.
  Never leave it empty by pretending you followed the briefing.

## Phase 4 - `features/INDEX.md`

Cut the product into features. One feature = one testable, deployable unit.
Split when it's a different entity, a different role, a different screen, or
independently shippable. Number them `PROJ-1 … PROJ-n`.

**Priority follows dependencies, not enthusiasm:**
- **P0** - something else cannot exist without it: auth, tenancy, app shell,
  the core entity's CRUD, the one flow that makes the product the product.
- **P1** - the product is usable without it but feels unfinished.
- **P2** - later. Say so and mean it.

Give each feature **one line of scope**: what is in it, and the nearest thing
that is deliberately not. "PROJ-7 Events Management" is a label, not a cut - the
line is what makes the checkpoint below worth holding. Acceptance criteria stay
out; that is `/write-spec` work.

Estimate each feature as **S / M / L** - relative size, not days. It is the
second input to the wave layout: an L feature alone in a wave beats three L
features in one.

Size the **delivery unit**, not only the business label. A feature must still be
possible to understand in one independent review and exercise in one QA pass. Use
these as review-budget tripwires, not as targets: more than 20 acceptance
criteria, 10 implementation tasks or 5 sequential batches means the feature is
probably an epic. Split it into vertical, separately mergeable slices, with hidden
or inert seams when the complete user flow cannot ship yet. An oversized unit may
survive only when the user explicitly accepts the review cost and the scope line
records why no safe slice exists. Relative S/M/L without an upper bound allowed a
57-criterion "M" feature; the label did not make its diff reviewable.

Calibrate the estimates before assigning them: define one concrete S, M and L
anchor for this product based on owned entities, screens, integrations and risky
state transitions. Then inspect the distribution. If more than half the features
have the same estimate, or none is S, the column is probably hiding bad cuts:
split oversized features, merge artificial slivers, or explain why the skew is
real. Do not force a cosmetic bell curve, but never leave an uninformative
distribution unexplained.

Then the **build order in waves**: wave 1 depends on nothing, wave *n* only on
waves before it. Features inside one wave can be built in parallel. Aim for
3–7 waves; more than that usually means the dependencies are guessed.

**Cut waves so they can be worked in parallel later.** Features in one wave will
eventually be picked up by concurrent agents, so within a wave, two features must
not need the same surface: the app shell, a shared type, the same entity's schema,
the same route. Where that collision is unavoidable, either pull the shared piece
out into its own earlier feature, or mark the two as serialized inside the wave
and say which goes first. Note the shared surfaces per wave - that note is what
makes an autonomous loop possible later without three agents fighting over one file.

**Wave 1 must be demoable.** Dependency order alone tends to produce a first
wave of auth + shell + empty database - three weeks with nothing to look at.
Pull the thinnest slice of the core flow into wave 1 so the product does its
one real thing end to end, however crudely. Name that slice explicitly.

Use the INDEX skeleton in [templates.md](templates.md): ID · feature · prio ·
status (all `Roadmap` in this planning pass) · depends on · effort · wave · spec link
(empty here - `/write-spec` fills it) · owner and branch (both empty in this planning pass,
claimed by whichever agent picks the feature up).

Write the **status ladder and the pick rule** into the file, so every later skill
and any loop reads them from one place.

The ladder moves forward once per lifecycle boundary, so the board says what may happen next:
`Roadmap` → `Spec` (/write-spec) → `Designed` (/tech-design, on approval) →
`Ready` (/tasks) → `In Progress` (/build) → `In Review` (built, /review and /qa) →
`Done` (/merge, after the merge it performs). A feature that gets cut goes to `Dropped` with the
reason in its row - deleting the row loses why it was ever wanted. `In Review`
covers the owned delivery loop - review, QA, corrections and CI - so findings send
work back to `/build` without bouncing the board.

A feature is pickable when its status is `Roadmap`, every feature it depends on is
`Done`, no owner is set, and nothing serialized before it in its wave is still
open. Claiming means setting owner and status in
one edit before any other work starts.

Plan for the loop, don't build it. No scheduler, no lock file, no runner - those
are a later feature, and they need nothing from this skill beyond these columns and
the parallel-safe wave cut.

**Checkpoint.** Present the feature list with the scope lines and the waves, and
get approval before Phase 5. Wrong cut here poisons everything downstream.

## Phase 5 - `docs/data-model.md`

- **Entities**: name, purpose in one line, key fields, owner (tenant/user/global).
- **Relations**: `A 1-n B`, in prose that a PM can read. Name the cascade
  behaviour where deletion matters.
- **Status/enum meanings**: every status value and what it actually means.
- **What is deliberately NOT an entity** - and what it is instead (a computed
  value, a column, a derived view, an enum, a file in storage). This section
  prevents half the over-modelling that follows.
- **Tenant isolation**: which entities carry the tenant key, and how isolation is
  enforced (database-level policies vs. application-level filtering). One decision,
  written once, obeyed by every later feature.
- **Language**: the term used for each concept, and the synonyms deliberately *not*
  used. Later specs and UI copy follow this list, so drift stops here.
- **Sketch**: one plain-text tree/box diagram of the entities. No SQL, no DDL.

## Phase 6 - `docs/journeys.md`

Entities are the nouns, features are the parts - journeys are the product actually
being used. Without this the plan is a pile of CRUD.

- **Signup to first value**: every step from landing on the page to the moment the
  user gets something out of the product. Name that moment. Count the steps before
  it - if it takes more than three, name one concrete step to remove, defer or have
  the operator complete beforehand, and state the revised count. Re-labelling five
  steps as three productive actions is not a cut.
- **The empty account**: what a brand-new tenant sees before any data exists.
  Empty states, sample data, guided setup, or an invite - pick one per screen.
- **Core journey per role**: one flow per role from Target users, in numbered steps,
  naming the entities touched and the features involved.
- **Recurring vs. one-time**: which journeys happen daily and which happen once.
  Daily ones decide the navigation; one-time ones must not clutter it.
- **Where it breaks**: for each journey, the one step most likely to lose the user.

## Phase 7 - `docs/access.md`

Roles and plans were decided in Phase 2. This is where they become checkable.

- **Roles**: every role, and who assigns it.
- **Permission matrix**: roles down, entities across, cells holding the allowed
  actions (create / read / own only / update / delete / none). Every cell filled -
  an empty cell is a decision nobody made.
- **Responsibility traceability**: compare every responsibility stated for a role
  in the briefing and PRD with the matrix. Either the matrix permits it, or the PRD
  and deviations table explicitly say why the product changed it. A later access
  document must not silently revoke a promised capability.
- **Plan gating**: which feature or limit belongs to which plan tier, and what a
  user hits when they exceed it (blocked, upsell, soft limit).
- **Cross-tenant rules**: what, if anything, is visible across tenants, and who
  may act on another tenant's data (support, admin, nobody).

Skip the plan-gating half only when Phase 2 established there is no monetization
yet - and say so in the file rather than leaving it out silently.

## Phase 8 - `docs/app-shell.md`

The frame every page sits in, so no later feature reinvents it.

- **Shells**: usually two - public/marketing and authenticated app. Say which.
- **Areas per auth state**: logged out, logged in, admin, and what each may see.
- **Layout regions**: header, primary nav, sub-nav, content, footer, notifications
  - including what stays identical on every sub-page.
- **Navigation**: the actual entries, their order, and their route.
- **Visual-source fidelity**: when a supplied mockup defines navigation order or
  group labels, preserve both. If product reasoning requires a change, record the
  old and new structure in the PRD deviations table and cite it here; do not let a
  reasonable redesign become a silent contradiction.
- **Page patterns**: list page, detail page, form page, empty state, error state,
  loading state - described once here, reused by every feature.
- **Headings & titles**: the h1 rule, the browser-title pattern, breadcrumbs.
- **UI support matrix**: the browser and viewport classes this product promises to
  support, and what is deliberately out of scope. An internal desktop tool does
  not inherit a mobile matrix by accident; a customer-facing product does not
  silently become desktop-only.
- **Route map**: every route including dynamic segments, the auth state it
  requires, and the feature that owns it.
- **Owner**: name the `PROJ-x` that builds this shell. It is a real feature and
  belongs in a wave, normally wave 1 or 2 - not "somehow part of everything".

## Phase 9 - `docs/design-system.md` *(only if visual input exists)*

Skip this file entirely when there is no mockup, screenshot or brand reference -
an invented design system is pure fiction. When there is one, read the values off
it: colors (as the token format the chosen stack wants, e.g. HSL for Tailwind
tokens), typography scale, radii, spacing, shadows, and the component inventory
visible in the mockup. Note explicitly what the mockup does *not* show.

## Phase 10 - `docs/local-dev.md`

Write down how it will run. Do not make it run.

1. **Ports**: check what is already taken (`lsof -i -P -n | grep LISTEN`). If the
   stack's defaults are occupied by other projects, allocate a free
   project-specific range and write it down. Never stop the other projects.
2. **Commands**: install, start, stop, reset, migrate and unit/integration test -
   one line each, as the developer will type them. Include the browser E2E entry;
   if its runner is still open, write `decided by /architecture` rather than
   inventing a command. Architecture replaces that marker with the exact local and
   CI entry points before scaffold starts.
3. **External accounts**: every third-party service the plan depends on, what it
   is for, whether a free tier covers the start, and what it costs after.
4. **`.env.local.example`**: every variable, one comment per line, placeholders
   for secrets. Mark which keys must stay server-side and why.
5. **Deploy target**: where frontend, backend and database go, which environment
   variables each needs, the build command, and the region - driven by whatever
   compliance constraint the PRD recorded.
6. **Who does the setup**: `PROJ-1`, built by `/scaffold`, wave 1. Put it on the
   board like any other feature - it is the one everything else depends on, not a
   footnote.

## Phase 11 - `CLAUDE.md`

Every later session - human or agent - starts in this repository knowing nothing.
This file is what it reads first, so it is the difference between a session that
orients itself in three tool calls and one that guesses.

Keep it **short and pointed**. It is not a summary of the plan; it is the map to
the plan plus the handful of rules that are not derivable from the documents.
Point to the living documents and instruct later sessions to read them rather than
repeating their contents. Use ordinary paths and prose, not harness-specific import
syntax: the generated context file must work in both Claude and Codex.

It carries:
- what this product is, in two sentences,
- a reading list of the living documents, scoped by the session's role as the
  skeleton shows: planning sessions read the plan completely, delivery sessions
  read their feature folder plus the named slices, sub-agents read only their
  brief. One flat "read everything" list is paid for by every session and
  sub-agent of every delivery round, which makes it the most expensive sentence
  in the repository,
- the commands, from `docs/local-dev.md`,
- the status ladder and who moves which rung,
- the vocabulary rule: the terms in `docs/data-model.md` are the terms, in code,
  in the interface and in commits,
- the working rule that matters most for an agent: **where the documents are
  silent, ask - do not invent**,
- what must never be touched: `.env.local`, real secrets, another feature's files
  while it is owned,
- and, when this repository is built unattended, the `/kaitersberg:build-loop`
  and `$kaitersberg:build-loop` invocation, where it stops, and how to ask it to
  start detached or inspect status. The skill resolves its bundled runner and
  status helper, so the product must not record a framework checkout or
  plugin-cache path. A session three weeks later starts in this repository knowing
  nothing; without this pointer it will run the pipeline by hand, or start the loop
  attached and kill it on the way out.

Use the `CLAUDE.md` skeleton in [templates.md](templates.md).

If the repository root already carries another harness's context file, write the
same content into it rather than leaving it stale - from here on every skill that
anchors something has to update both, and two context files that disagree are
worse than one that is merely terse.

## Phase 12 - Report

Final message, exactly this shape:

```
## What is in the project now

| File | Contents |
|---|---|
| docs/PRD.md | Vision, target users, N features, success criteria, constraints, non-goals - plus a table of every deliberate deviation from the briefing |
| features/INDEX.md | N features, all on `Roadmap`, each with a scope line, priority, dependencies and the build order in M waves |
| docs/data-model.md | N entities, relations, status meanings - and what deliberately is *not* an entity |
| docs/journeys.md | Signup to first value in N steps, the empty account, one core journey per role |
| docs/access.md | Roles, the full permission matrix, plan gating, cross-tenant rules |
| docs/app-shell.md | Shells, areas per auth state, layout regions, page patterns, route map. Owner: PROJ-x |
| docs/design-system.md | (only when a mockup was supplied) |
| docs/sources/INDEX.md | (only when material from outside arrived) N sources, and what rests on each |
| docs/local-dev.md | Ports, commands, external accounts, deploy target. Owner: PROJ-x |
| CLAUDE.md | What every session reads first: the reading list, the commands, the rules |

Plus: `.env.local.example`.

## Decisions you should look at
<the 3–5 deviations and open risks most likely to be wrong. Name them here, not
only in the file - this is the part worth arguing about now rather than in wave 4.>

## Next step
`/architecture` - decide the house style once. Then `/scaffold`, then `/write-spec PROJ-2`.
```

Then commit:
```
feat: Plan the product - PRD, feature map, data model, app shell

- PRD with vision, constraints, non-goals, risks and briefing deviations
- N features on the roadmap in M build waves, wave 1 demoable
- Data model with N entities, journeys and permission matrix
- App shell and local dev plan owned by PROJ-x
```

## Checklist
- [ ] Briefing and all mockups actually read
- [ ] Material from outside filed in `docs/sources/` with what rests on it - or none arrived
- [ ] Open questions asked once, with a recommended option
- [ ] PRD complete, incl. success criteria that are measurable and non-functional ones
- [ ] Deviations table filled - not empty
- [ ] Risks and open questions listed, each with an impact
- [ ] Features cut by single responsibility, prio derived from dependencies
- [ ] One scope line per feature, naming what is in and what is not
- [ ] Every feature sized S/M/L
- [ ] Every feature fits the review budget, or its explicit exception and reason are recorded
- [ ] S/M/L anchors written; a skewed estimate distribution recut or explained
- [ ] Build order in waves, every dependency pointing backwards only
- [ ] Wave 1 contains a demoable slice of the core flow, named explicitly
- [ ] Per wave: shared surfaces named, collisions either split out or serialized
- [ ] Pick rule written into `features/INDEX.md`
- [ ] User approved the feature cut before the rest was written
- [ ] Data model incl. the "not an entity" section, tenant isolation and a sketch
- [ ] Signup-to-first-value journey counted in steps
- [ ] More than three first-value steps has a concrete cut and revised count
- [ ] Permission matrix has no empty cells
- [ ] Every role responsibility in the briefing/PRD is permitted or declared as a deviation
- [ ] App shell has a route map and a named PROJ-x owner with a wave
- [ ] Mockup navigation order and groups preserved, or the deviation is explicit
- [ ] Design system only if visual input existed
- [ ] Local dev planned, `.env.local.example` written, `.env.local` untouched
- [ ] `CLAUDE.md` written: reading list, commands, status ladder, ask-do-not-invent;
      unattended repositories name build-loop's detached, status and follow modes
- [ ] Any other harness context file in the root carries the same content, not an older one
- [ ] No code, no config files, no services started
