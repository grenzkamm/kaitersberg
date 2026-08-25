# Tech Design Template

Written to `features/PROJ-x-<short-name>/design.md`, next to `spec.md`.
Headings shown in English - write them in the language of the specification.
Delete a section with a one-line reason rather than leaving a placeholder.

---

```markdown
# PROJ-x: <Feature name> - Technical design

**Based on:** [spec.md](spec.md)
**Status:** Awaiting approval
**Created:** YYYY-MM-DD

## In short
<Three to five sentences. What exists after this is built, and why. Written for
somebody who will never open the code.>

## What changes for whom
| Role | Can do afterwards what they could not before | Notices what else |
|---|---|---|

## Roles and rights
| Action | Administrator | User | <other role> | Why the difference |
|---|---|---|---|---|
| <action from the spec> | yes / no / own records only | | | |

<Every cell filled. "No difference" is an answer and belongs in the table.>

**Rules that apply throughout this feature:**
- <e.g. a user sees only the records of their own team; the administrator sees the
  whole tenant>

## Data
### <Entity> - <new entity | existing entity, extended>
| Field | Means | Type | Required | Default | Rule | Personal data | New |
|---|---|---|---|---|---|---|---|
| <name> | <in business terms> | <from the type vocabulary> | yes/no | | <validation, limits> | no / yes / special category | yes/no |

**Status values**
| Value | Means in the business | Set by |
|---|---|---|

**Relationships**
- <Entity> belongs to <Entity> - <what happens when the other one is deleted>

**Deliberately not stored**
| Not stored | Why | Where it comes from instead when needed |
|---|---|---|

## Rules that always hold
- <what must be true before and after every action in this feature, no matter who
  triggered it>

## Flow
<The main scenario as numbered steps, in the words of the business. No screens
that do not exist, no technical steps.>

1. …
2. …

**When it goes wrong**
| Goes wrong | What the user sees | What happens to the data |
|---|---|---|

## Component structure
<The interface as a tree. Mark every part: reused, extended, or new. A part marked
new must not already exist elsewhere in the product.>

​```
<Page>
 +-- <Component A>            reused (design system)
 +-- <Component B>            extended - <what is added>
 |    +-- <Component C>       new
 +-- <Empty state>            reused (app shell pattern)
​```

| New component | Why nothing existing fits |
|---|---|

## Pages and routes
| Route | Page pattern | What is on it | New or reused | In the route map? |
|---|---|---|---|---|

## Abuse protection
| Where a user reaches in | Check that sits before it | Limit | What the abuser sees | Recorded? |
|---|---|---|---|---|

- **Tenant isolation here:** <how it is enforced for these records>
- **Limits in numbers:** <size, rate, count - a limit without a number is not one>

## Configuration
| Setting | Does what | Default | Changed by | Per tenant or installation |
|---|---|---|---|---|

<A value that will never change is not configuration. Say so and hard-code it.>

## Environment variables
| Variable | Purpose | Example | Server-side only | Why |
|---|---|---|---|---|

<Every one of these is added to `.env.local.example` and `docs/local-dev.md`.>

## Secrets and keys
| Secret | Protects what | Where its value comes from | Separate from | Rotatable - and what happens to stored values |
|---|---|---|---|---|

<Never in a payload, an output or a log. Example values only in the repository;
`.env.local` is never written by anybody.>

## Dependencies
| Package | Does what | Replaces | Why not the standard library, the platform, or what is already installed | Licence |
|---|---|---|---|---|

<A row without the fourth column does not get approved.>

## Technical decisions
| Decision | Alternatives | Why this one | What it costs later |
|---|---|---|---|

## Outside contact
| Service | What is sent | What comes back | If it is unreachable |
|---|---|---|---|

<"None" is a valid and welcome answer.>

## Migration
<Only when this feature changes the shape of stored data. "No migration" is a valid
and welcome answer.>

| Step | What it does | Existing rows | Destructive? |
|---|---|---|---|

- **Backfill comes from:** <the source of the value, or "default only">
- **Reversible?** <yes and how | no, and what `docs/architecture.md` requires>

## Effect on what already exists
- **Existing records:** <what happens to them, and what value new fields get>
- **Records that do not fit the new rules:** <left alone, corrected, flagged>
- **Other features:** <which ones notice this, and how>
- **Reversible?** <what stays behind if this is rolled back>

## Limits and assumptions
| Assumes | Stops working when |
|---|---|

## Corrections to the plan
<What this design added beyond the plan, and which document was corrected.
"Nothing" is the good case and is worth stating.>

| Document | What was corrected |
|---|---|

## Coverage of the specification
| AC | Where it is answered here |
|---|---|
| AC-1 | <section> |

<Every AC of the spec has a row. A missing row is a gap, not an oversight.>

## To decide
| Question | Options | Recommendation | Cost of getting it wrong |
|---|---|---|---|

## Approval
- **Approved by:** <name>
- **On:** YYYY-MM-DD
- **Conditions:** <what must still be true, or "none">
```
