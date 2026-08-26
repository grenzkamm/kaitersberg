# Init Templates

Skeletons for the documents `$plan-product` writes. Fill them, don't
ship them with placeholders. Delete any section that genuinely does not apply
and say why in the deviations table. Headings are shown in English - render them
in the language the user briefed you in.

---

## `docs/PRD.md`

```markdown
# Product Requirements Document - <product name>

## Vision
<2–3 sentences: what this is and why it exists.>

## Target users
| Role | Who | Needs | Pain point today |
|---|---|---|---|

## Core features
| Prio | PROJ-x | Feature | Why |
|---|---|---|---|

## Success criteria
- <measurable. number, timeframe, threshold.>

## Constraints
| Area | Decision | Why |
|---|---|---|
| Frontend | | |
| Backend | | |
| Database | | |
| Auth | | |
| AI | | |
| Payments | | |
| Hosting / deploy | | |
| Expected scale | <tenants / users / records in year 1> | |
| Performance | <target response time> | |
| Availability | <target, and what downtime costs> | |
| Data retention | <how long, what gets deleted> | |
| Compliance | <GDPR, hosting region, audit needs> | |
| Backups | <frequency, restore target> | |

## Non-goals
- <what is deliberately not built - and when it would be picked up.>

## Risks & open questions
| Risk / question | Impact if it goes wrong | Settled by |
|---|---|---|

## Deliberate deviations from the briefing
| Briefing said | The plan does | Why |
|---|---|---|
```

---

## `features/INDEX.md`

```markdown
# Feature Index

> Central overview. Kept up to date by the skills automatically.

## Status
Lifecycle rungs move forward once. Delivery details inside `In Review` live in the
feature artifacts and persisted loop state, so findings do not bounce the board.

| Status | Means | Set by |
|---|---|---|
| `Roadmap` | Planned as a row, nothing written yet | $plan-product |
| `Spec` | Specification written | $write-spec |
| `Designed` | Technical design approved | $tech-design |
| `Ready` | Task list cut, may be built | $tasks |
| `In Progress` | Initial build before the first full review | $build |
| `In Review` | Owned delivery loop: review, test, corrections and CI | $build |
| `Done` | Merged into the main branch | $merge, which merges and cleans up |
| `Dropped` | Cut from the product | whoever cuts it, with the reason in the row |

Findings send work back to `$build` without moving the owned feature backwards on
the board.

## Features
| ID | Feature | Prio | Status | Depends on | Effort | Wave | Spec | Owner | Branch |
|---|---|---|---|---|---|---|---|---|---|
| PROJ-1 | | P0 | Roadmap | - | M | 1 | - | - | - |

`Spec` stays `-` until `$write-spec` creates the feature folder, then holds the
link to `features/PROJ-x-<short-name>/spec.md`.
`Owner` and `Branch` stay `-` until an agent claims the feature.

## Effort calibration
| Size | Product-specific anchor |
|---|---|
| S | <smallest independently shippable change in this product> |
| M | <multiple states or surfaces, no dominant integration risk> |
| L | <multiple owned surfaces, integration or high-risk state machine> |

**Distribution check:** <counts per size; if more than half share one size or no
feature is S, say what was recut or why the skew is real>

## Pick rule
A feature is pickable when **all** of these hold:
1. Status is `Roadmap`
2. Every feature under `Depends on` is `Done`
3. `Owner` is `-`
4. Nothing serialized before it in its wave is still open

Claiming = set `Owner` and `Status: In Progress` in one edit, before doing
anything else. Release = clear `Owner` if the work is abandoned.

## Scope per feature
- **PROJ-1 <name>** - in: <what this feature covers>. not: <the nearest thing it
  does not cover, and which PROJ-x has it instead>

## Build order
**Wave 1 - <theme>:** PROJ-1, PROJ-2 - <what this unlocks>
**Demoable after wave 1:** <the thinnest end-to-end slice of the core flow>
**Wave 2 - <theme>:** …

## Parallel safety
| Wave | Runs in parallel | Serialized | Shared surface |
|---|---|---|---|
| 1 | PROJ-1, PROJ-2 | PROJ-3 after PROJ-1 | <app shell / shared types / entity X> |

Next free ID: PROJ-<n+1>
```

Only `PROJ-x` rows here. Full specs come from `/requirements`,
one at a time, when the feature is actually next.

---

## `docs/data-model.md`

```markdown
# Data model

## Entities
### <Entity>
- **Purpose:** <one sentence>
- **Owned by:** <tenant | user | global>
- **Fields:** <the important ones, not all of them>
- **Status values:** `<value>` = <meaning>

## Relations
- <A> 1-n <B> - <in prose, incl. what happens on delete>

## Tenant isolation
- **Key on:** <which entities carry the tenant reference>
- **Enforced by:** <database policies | application filter> - <why>

## Deliberately NOT an entity
| Non-entity | Instead | Why |
|---|---|---|

## Language
| We call it | We do not call it | It means |
|---|---|---|

## Sketch
<plain-text tree, fenced, e.g.>
    <Tenant>
     +-- <Entity A>
     |    +-- <Entity B>
     +-- <Entity C>
```

---

## `docs/app-shell.md`

```markdown
# App shell

**Owner:** PROJ-x - <feature name>, wave <n>

## Shells
| Shell | For | Contains |
|---|---|---|
| Public | Logged out | |
| App | Logged in | |

## Areas per auth state
| State | Sees | Does not see |
|---|---|---|

## Layout regions
| Region | Contents | Identical on every sub-page? |
|---|---|---|

## Navigation
| Entry | Route | Visible to |
|---|---|---|

**Visual-source fidelity:** <source and preserved group/order, or the PRD deviation
that authorizes a change>

## Route map
| Route | Auth state | Owned by | Notes |
|---|---|---|---|
| `/` | public | PROJ-x | |
| `/<resource>/:id` | logged in | PROJ-x | |

## Page patterns
- **List page:** <structure, empty state, loading state, error state>
- **Detail page:** …
- **Form page:** …

## Headings & titles
- h1: <rule>
- Browser title: `<pattern>`
- Breadcrumbs: <yes/no, pattern>

## UI support matrix
| Class | Browser / device | Viewport | Required | Why |
|---|---|---|---|---|
| Primary desktop | <browser family> | <width × height> | yes | |
| <mobile / tablet / second browser, when promised> | | | | |

**Deliberately unsupported:** <environment and why>
```

---

## `docs/journeys.md`

```markdown
# Journeys

## Signup to first value
**First value is:** <the moment the user gets something out of this>
**Steps to get there:** <n>

| # | Step | Screen | User does | System does |
|---|---|---|---|---|

**Concrete cut because this is more than three steps:** <remove, defer or
operator-preconfigure one step> → **revised count:** <n>

<Delete this line only when the original count is three or fewer.>

## The empty account
| Screen | What a brand-new tenant sees | Empty state / sample data / guided setup |
|---|---|---|

## Core journey per role
### <Role>
1. <step> - entities: <...> - feature: PROJ-x
**Runs:** <daily | weekly | once>
**Most likely to lose the user at:** <step> - <why>
```

---

## `docs/access.md`

```markdown
# Access

## Roles
| Role | Assigned by | Scope |
|---|---|---|

## Permission matrix
Actions: `C` create, `R` read all, `Ro` read own, `U` update, `D` delete, `-` none.

| Role \ Entity | <Entity A> | <Entity B> |
|---|---|---|
| <Role> | | |

## Responsibility traceability
| Responsibility promised in briefing / PRD | Role | Allowed by matrix | If no, PRD deviation |
|---|---|---|---|
| <responsibility> | <role> | <yes/no, action and entity> | <deviation link or -> |

## Plan gating
| Plan | Features | Limits | On exceeding |
|---|---|---|---|

## Cross-tenant rules
- <what is visible across tenants, who may act, and who may not>
```

---

## `docs/local-dev.md`

```markdown
# Local dev & deploy

**Setup owned by:** PROJ-x, wave <n>

## Stack & versions
| Part | Package | Version | Docs for this version |
|---|---|---|---|

<Left empty here. $scaffold resolves the current stable release of each part when
it installs, then fills this from the lockfile - what actually landed, not what was
planned or remembered. Every later skill checks an API against this table instead of
against what it remembers. A part deliberately held on an older line carries the
reason in the Docs column.>

## Ports
| Service | Port | Note |
|---|---|---|

## Commands
| Purpose | Command |
|---|---|
| Install | |
| Start | |
| Reset data | |
| Test | |
| Browser E2E | |

## External accounts
| Service | Used for | Free tier enough? | Cost after |
|---|---|---|---|

## Environment variables
| Variable | Value | Server-side only? |
|---|---|---|

## Deploy
| Part | Target | Build command | Region | Env vars |
|---|---|---|---|---|
```

---

## `docs/sources/INDEX.md` *(only when material from outside exists)*

```markdown
# Sources

Material that came from outside and that the product has to obey or refer to:
regulations, standards, a supplier's data sheet, a contract, a mockup, the notes
from the meeting where something was settled. The file is kept in
`docs/sources/` where its licence allows that, and linked where it does not.

**No code goes in here.** The repository is its own source, and a copy of it is a
second original that is stale immediately.

| ID | What it is | Where | Dated | What rests on it | Last checked |
|---|---|---|---|---|---|
| S-1 | <what this document is, and who issued it> | `docs/sources/<file>` or <link> | <the date on the document> | <the rules, fields or criteria that cite it> | <when somebody last confirmed it is still the current version> |

Next free ID: S-2

A document that changes outside this repository changes silently. The last column
is the only thing that makes that visible, and $audit reads it.
```

---

## `docs/design-system.md` *(only when a mockup exists)*

```markdown
# Design system
> Read off <source>. Not invented.

## Colors
| Token | Value | Used for |
|---|---|---|

## Typography
| Role | Font | Size / weight / line-height |
|---|---|---|

## Radii, spacing, shadows
## Components visible in the mockup
## What the mockup does not show
- <open points to decide later>
```

---

## `AGENTS.md`

Short on purpose. Point to the documents and require reading them; do not restate
them or rely on harness-specific import syntax.

```markdown
# <Product>

<Two sentences: what this is and who uses it.>

## Read these

Read by the role of your session, not everything every time - the delivery half of
the pipeline runs many sessions per feature, and a reading list every one of them
pays for in full is the largest avoidable cost in the loop:

- **Planning or designing** (product plan, spec, design, board changes): read
  completely - `docs/PRD.md`, `features/INDEX.md`, `docs/data-model.md`,
  `docs/access.md`, `docs/app-shell.md`, and `docs/architecture.md` once it exists.
- **Building, reviewing or testing one feature**: the feature's own folder
  (`features/PROJ-x-<name>/`), your feature's row and the pick rule in
  `features/INDEX.md`, the commands in `docs/local-dev.md`, and from
  `docs/architecture.md` the gate commands, conventions and budgets. The spec and
  design already carry the plan answers that apply here; read a plan document only
  when they point at it.
- **A sub-agent given a task brief**: only what the brief hands you. The brief was
  cut so nothing else is needed.

## Commands
| Purpose | Command |
|---|---|
| Install | |
| Start | |
| Test | |
| Browser E2E | |
| Migrate | |
| Reset data | |

<From docs/local-dev.md. Ports: <the range>.>

## How work moves
`Roadmap` → `Spec` → `Designed` → `Ready` → `In Progress` → `In Review` → `Done`

Lifecycle rungs move forward once: $write-spec · $tech-design · $tasks · $build ·
$merge, which merges it. Review, QA, corrections and CI share `In Review`. The board is `features/INDEX.md`; a feature is claimed by
setting owner and status in one edit before any work starts.

Each feature keeps everything in `features/PROJ-x-<name>/`: spec, design, tasks,
review, test report, pull request body, evidence.

## Unattended runs
<Fill this in if this repository is built unattended, or delete it with the line
"built one skill at a time" - a heading nobody filled reads as "nobody looked".

Name `/kaitersberg:build-loop PROJ-x` for Claude and
`$kaitersberg:build-loop PROJ-x` for Codex as the commands that run build, review,
qa and optionally pr as separate sessions, and say where the loop stops. The skill
resolves the runner inside its installed plugin; this product repository must not
record a framework checkout or plugin-cache path. Say that restarting resumes the
persisted stage, and name the explicit state-reset and manual import-stage controls
supplied by the framework.

Name its `detached`, `status` and `follow` modes. A detached handoff reports the
tmux session plus the state, event-log, durable launcher-log and exit-code paths;
tmux accepting the session leaves current state unknown and is not a completed
delivery. A run takes hours, and an agent that starts it attached to a chat session
takes it down again when that session ends, with the stage in flight uncommitted in
the worktree.>

## Rules
- **Where the documents are silent, ask. Do not invent.** An invented behaviour is
  a defect that passes review because nobody specified otherwise.
- **The words in `docs/data-model.md` are the words** - in code, in the interface,
  in commits. No synonyms.
- **Never touch `.env.local` or real secrets.** Print values for the user to paste.
- **Never work in another feature's files while it has an owner.**
- **Never build on the main branch.** Every feature gets its own worktree.
- Commits: `feat(PROJ-x): …`, `fix(PROJ-x): …`, `docs(PROJ-x): …`, and on a bug
  branch `test(BUG-n): …` before `fix(BUG-n): …`. One commit per task or step,
  never one at the end of a feature.
```
