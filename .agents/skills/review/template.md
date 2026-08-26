# Review Template

Written to `features/PROJ-x-<short-name>/review.md`. Headings shown in English -
write them in the language of the project's documents.

---

```markdown
# PROJ-x: <Feature name> - Review

**Reviewed:** YYYY-MM-DD   **Branch:** feature/PROJ-x-<name>   **Commit:** <sha>
**Mode:** Full | Delta from <previous reviewed sha>   **Scope reason:** <why this is sufficient>
**Against:** [spec.md](spec.md) · [design.md](design.md)
**Diff:** +A −B across C files

## Verdict
**Approved | Approved with notes | Changes required**

<One or two sentences. If changes are required, name the single finding that
decides it.>

| Severity | Count |
|---|---|
| Blocking | |
| Note | |

## What was expected
<Written from the spec and the design **before** the diff was opened. Kept in the
report so the next reader can see what the review was measured against.>

| Expected | Found |
|---|---|
| AC-1: <one line> | <holds / does not hold - where> |
| Field `<name>`: <type, rule> | |
| Only `<role>` may `<action>` | |
| Limit: <number> | |
| Reuses `<component>` | |

## Findings
### F-1 - <title> · Blocking | Note
- **Where:** `path/to/file.ts:123`
- **Breaks:** AC-n | <design section> | <rule>
- **What is wrong:** <one sentence>
- **Concrete failure:** <which input, which state, which result>
- **Smallest fix:** <what would settle it - not how you would have written it>

## Checked and sound
<What was examined and found correct. Short, but present: a review that only lists
problems does not tell the reader what was actually looked at.>

- <area> - <what was verified>

## Could not be checked
| What | Why | Who or what could |
|---|---|---|

<A review that hides its blind spots is worse than a short one that names them.>

## Next
- Changes required → keep the owned feature `In Review`; `$build` works these
  current findings, then replaces this review again **in a fresh session**.
- Otherwise → `$qa`.
```
