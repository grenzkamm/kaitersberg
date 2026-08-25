# Pull Request Body Template

Written to `features/PROJ-x-<short-name>/pr.md` and used as the pull request
description. Headings shown in English - write them in the language of the
project's documents. Delete a section with a one-line reason; an empty heading in
a pull request reads as "not considered".

---

```markdown
## PROJ-x - <Feature name>

<Two sentences from the spec's *Why*: what this does and which problem it solves.>

**Spec:** [spec.md](features/PROJ-x-<name>/spec.md) ·
**Design:** [design.md](.../design.md) ·
**Review:** [review.md](.../review.md) ·
**Test report:** [qa.md](.../qa.md)

## What is in it
- <the outcomes, in the words of the spec>

**Deliberately not in it:** <the "not" half of the scope, and which PROJ-y has it>

## Acceptance criteria
| AC | Requires | Verdict | Proven by |
|---|---|---|---|
| AC-1 | <one line> | ✅ | `AC-1 <test name>` |
| AC-5 | | ✅ manual | Screenshot in `evidence/` |

<Every AC of the spec. Manual ones marked manual - not quietly folded into "green".>

## Verify it yourself
1. `git checkout feature/PROJ-x-<name>` · `<install>` · `<migrate>` · `<seed>`
2. Log in as `<role>` (<credentials from the example data>)
3. <exact steps>
4. **Expect:** <the one path that proves it works>
5. **Then** try <the refused path> as `<other role>` - **expect:** <the refusal>

## Data and migration
- **New fields:** <entity.field - type, required, default>
- **Existing rows get:** <backfill value, or "not applicable">
- **Status values:** <new ones and what they mean>
- **Reversible:** <what a rollback leaves behind>

## Roles and permissions
| Action | Administrator | User | Changed? |
|---|---|---|---|

<Only the rows this feature changed.>

## Personal data
**Classification:** none | personal data | special category
<When not "none": which fields, on what legal basis, kept how long, erased how.>

## Security
- **Protections added:** <with their numbers>
- **Adversarial pass:** <result from qa.md - what was probed and what held>

## Before this can run
| Needed | Value | Who sets it |
|---|---|---|
| <environment variable> | <placeholder - never the real secret> | |
| <configuration> | | |
| <new dependency> | <version, why it was needed> | |

<"Nothing" is the good answer and worth stating.>

## Screens
<Screenshots and the recording from `evidence/`. One image beats the paragraph
describing it.>

## Deviations and decisions
| What differs from the design | Why | Written back to |
|---|---|---|

<Including the ones nobody objected to. A silent deviation is the one that hurts
in six months.>

## Risk and rollback
- **What could break:** <the honest answer>
- **Noticed by:** <which other features touch this>
- **Rollback:** <how, and what stays behind>

## Follow-ups
| PROJ-y | What was left | Why it was left |
|---|---|---|

<Each one a real row in features/INDEX.md. A follow-up living only in this
description is forgotten by Friday.>

## Checks
lint ✅ · types ✅ · unit <n> ✅ · integration <n> ✅ · e2e <n> ✅
**Coverage:** <n>% (floor <m>%, was <k>%)
<Real numbers. If something is red or skipped, it says so here. If coverage fell,
say which code arrived without a test and why.>
**Suppressions added:** <each with its reason, or "none">
```
