# Spec Template

The skeleton `$write-spec` fills, written to
`features/PROJ-x-<short-name>/spec.md`. Headings shown in English - write them in the
language of the project's existing documents. Delete a section you cannot fill,
with a one-line reason. Never leave a placeholder standing.

---

```markdown
# PROJ-x: <Feature name>

**Status:** Planned
**Priority:** P0 | P1 | P2   **Effort:** S | M | L   **Wave:** <n>
**Created:** YYYY-MM-DD   **Last updated:** YYYY-MM-DD

## Why
<Two sentences: which problem from the PRD this solves, and which success
criterion it serves. If it serves none, say so - that is a finding.>

**Journey:** <which step of which journey from docs/journeys.md>

## Scope
**In:** <what this feature covers>
**Not:** <the "not:" half of the scope line from INDEX.md, verbatim, plus
whatever was cut during this session - each with the PROJ-x that has it instead>

## Dependencies
- **Requires:** PROJ-y (<why exactly - which entity, which route, which role>)
- **Unlocks:** PROJ-z

## Roles
| Role | Does what here |
|---|---|
<from docs/access.md - no new roles invented here>

## User stories
- **US-1** - As a <role>, I want to <action>, so that <purpose>.
- **US-2** - …

## Acceptance criteria

### Happy path
**AC-1 - <one-line title>** (US-1)
- **Given** <state that already exists, entities named with their status>
- **When** <exactly one action by one named role>
- **Then** <what the actor sees>
- **And** <what is stored or changed>

### Validation
**AC-2 - <title>** (US-1)
- **Given** …
- **When** …
- **Then** <refused, with which message>
- **And** <nothing is stored>

### Permissions
**AC-3 - <role> may not <action>** (US-2)
- **Given** …
- **When** …
- **Then** …

### Empty state / first use
### Concurrency and duplicates
### Failure of a dependency
### Limits

## Data
| Entity | Read | Written | New fields needed |
|---|---|---|---|
<from docs/data-model.md. A new field here is a change to the data model -
note it, and say whether the model document needs updating.>

**Status transitions:** `<from>` → `<to>`, triggered by <what>

## UI
| Route | Page pattern | Owned by |
|---|---|---|
<from docs/app-shell.md; a new route belongs in the route map there too>

- **Empty state:** <what the user sees, and the one action offered>
- **Loading:** <as per the app shell pattern, or the deviation and why>
- **Error:** <what is shown, what the user can do next>
- **Components:** <existing ones from the design system; new ones named as new>

### UI test contracts
| AC | Route | Role | Starting fixture | Required viewport(s) | User-visible result |
|---|---|---|---|---|---|
| AC-x | | | <named example data below> | <from docs/app-shell.md> | |

<One row for every E2E or manual UI criterion. This is observable behaviour, not
selectors or test code.>

## Example data
<Concrete records with real values, used by every scenario above and by the tests.
Without this each test invents its own values and they drift apart.>

| Name | Record | Values |
|---|---|---|
| `<fixture-name>` | <Entity> | <the actual values, not "a valid name"> |

## Texts and formats
<The exact strings. An agent that has to invent an error message invents a
different one than the rest of the product uses.>

| Key | Text |
|---|---|
| <error/empty/button key> | "<the literal text>" |

- **Numbers:** <decimal separator, thousands separator, decimal places>
- **Dates and times:** <format, time zone, what "today" means>
- **Amounts and units:** <currency, unit, where it is placed>

## Side effects
<Everything that happens besides writing to the database. An agent only builds
what is written down.>

| Trigger | Effect | Recipient / target | Failure behaviour |
|---|---|---|---|
| <AC-x> | <mail, notification, job, file, external call> | | <retry, ignore, surface> |

## Migration
<What happens to data that already exists when this ships.>

- **New fields on existing rows:** <default value, or backfilled from what>
- **Existing records that do not fit the new rules:** <left alone, corrected, flagged>
- **Reversible?** <what a rollback would leave behind>

## Where this lives
<Orientation only - the design is $architecture's job. Names the existing places
so nothing gets built twice.>

| Concern | Existing place to extend | Or new |
|---|---|---|

## Accessibility
- **Keyboard:** <the whole flow reachable without a mouse - name the order>
- **Focus:** <where focus goes after the action, and after an error>
- **Roles and names:** <inputs, controls and landmarks expose the role, label or
  accessible name a user and an accessibility-first test can identify>
- **Feedback:** <errors and status changes are announced, not only coloured>
- **Reflow:** <what must remain usable at the required narrow viewport and at 200%
  zoom, or why this does not apply>

### Forms
<Delete with a one-line reason when the feature has no form.>

- **Labels and instructions:** <how each remains perceivably associated with its field>
- **Failed submission:** <entered values preserved; errors announced; focus moves to the first error or an error summary>
- **Required and invalid:** <how these states remain understandable without colour>

## Edge cases
| Case | Behaviour |
|---|---|

## Personal data
**Classification:** none | personal data | special category (Art. 9 GDPR)

<When "none": one line saying which records this feature touches and why no
person stands behind them. Delete the rest of this section.>

| Field | About whom | Why it is needed | Could the feature work without it? |
|---|---|---|---|

- **Legal basis:** <contract | legal obligation | consent | legitimate interest> - <one line>
- **Purpose:** <what it is used for; using it for anything else is a new purpose>
- **Who may see it:** <roles from docs/access.md, and who explicitly may not>
- **Retention:** <how long, counted from what, and what happens then - deletion or anonymisation>
- **Erasure:** <what happens to these records when the person asks to be deleted;
  name what must survive for legal reasons and how it survives without the person>
- **Export:** <how this data leaves the system when the person asks for it>
- **Processors:** <every external service this data reaches - none is an answer>
- **Free text:** <does this feature have a field a user can type anything into?
  Then it can contain personal or special-category data. Say how that is handled.>

## Security
| Threat | What stops it | Scenario |
|---|---|---|
| Foreign tenant's record addressed by ID | | AC-x |
| Role does what only a higher role may | | AC-x |
| Hostile or oversized input | | AC-x |
| Action repeated automatically | | AC-x |
| <feature-specific: upload, export, link sharing, external call> | | AC-x |

- **Trust boundary:** <where untrusted input enters this feature, and where it is validated>
- **Rendered elsewhere:** <which fields of this feature are printed, exported or
  shown in another context - those are the ones that carry injected content out>
- **Secrets:** <any key this feature needs, and why it never reaches the client>
- **Audit:** <which actions here are recorded, with who and when - and confirm the
  audit record does not itself store more personal data than the action did>

## Non-functional
- **Performance:** <target for the operation that matters, with a number - the
  budget from `docs/architecture.md` for this kind of path, or stricter>
- **Volume:** <how many records this must stay usable with>
- **Audit:** <what must be traceable afterwards, and for how long>
- **Plan gating:** <from docs/access.md, or "none">

## Decisions made in this session
| Question | Decision | Why | Decided by |
|---|---|---|---|

## Open questions
| Question | Blocks | Who answers |
|---|---|---|

## Test plan
| AC | Level | Test name |
|---|---|---|
| AC-1 | Integration | `AC-1 <short title>` |
| AC-2 | Unit | `AC-2 <short title>` |

Every test carries its AC number in its name, so a failing test names the
criterion it broke and `$qa` can map results back without guessing.

**Manual checks:** <what no test can cover - print output, external service,
look and feel. Do not put observable browser behaviour here merely because no
automated browser harness exists.>

## Definition of Done
- [ ] Every AC passes at its level
- [ ] Permission scenarios verified for every refused role
- [ ] Tenant isolation verified with a real foreign ID, not a mocked one
- [ ] Retention and erasure behaviour verified, if personal data is involved
- [ ] Fields collected match the personal-data table - nothing extra slipped in
- [ ] Empty, loading and error state present per the app shell
- [ ] Every E2E/manual UI criterion has a complete UI test contract
- [ ] Automated browser criteria pass in every required project from the app-shell support matrix
- [ ] New routes added to the route map in docs/app-shell.md
- [ ] Data model document updated if fields were added
- [ ] `features/INDEX.md` status updated

---
**Beside this file:** `design.md` ($tech-design), `tasks.md` ($tasks),
`review.md` ($review), `qa.md` + `evidence/` ($qa), `pr.md` ($pr) - each written by
its own skill, none created empty.
```
