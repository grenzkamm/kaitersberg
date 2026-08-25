# Bug Template

One file per bug: `bugs/BUG-n-<short-name>.md`. A bug that needs sub-documents was
a feature. Headings shown in English - write them in the project's language.

---

```markdown
# BUG-n: <what goes wrong, in one line>

**Status:** Open | Reproduced | Fixed | Closed | Not reproducible | Not a bug
**Severity:** Critical | Major | Minor | Cosmetic
**Reported:** YYYY-MM-DD by <who>   **Affects:** <roles, tenants, since when>
**Feature:** PROJ-x   **Branch:** fix/BUG-n-<short-name>

Critical means: data loss, a hole in the isolation, personal data where it must not
be, or one user able to act as another.

## Expected vs. observed
- **Expected:** <from spec.md AC-n, or from design.md - name the document>
- **Observed:** <what actually happens>
- **Consequence:** <what it costs while it is open>

## Reproduction
1. <step, with named data>
2. …
**Happens:** always | sometimes (<how often, under what condition>)
**Environment:** <local | staging | production>, <version>

<If no loop could be built: what was tried, which conditions could not be
recreated, what would settle it - access, a captured artefact, permission to
instrument. Then the file stops here.>

## The loop
- **Command:** `<the one command, runnable without a person>`
- **Asserts:** <the exact symptom it goes red on>
- **Failing output:**
  ```
  <pasted from the run>
  ```
- **Minimised to:** <what is left once everything not load-bearing was cut>

## Cause
- **Candidates considered:** <the ranked list, and which one it turned out to be -
  the next reader learns more from this than from the fix>
- **In one sentence:** <the decision that is wrong>
- **Where:** `path/to/file.ts:123`
- **Same cause also reached through:** <the other callers or paths - or "none,
  checked <n> callers">

## Fix
- **What changed:** <one or two sentences>
- **Where:** <the shared place, not each caller>
- **Regression test:** `BUG-n <short title>` - <level>, seen failing first

## Existing damage
| Records affected | State now | What was done |
|---|---|---|

<"None" is an answer, but only after looking.>

## Also checked
<The neighbouring paths, and - for isolation, permission or personal-data bugs -
what an adversarial look turned up.>

## Documents corrected
| Document | What was wrong or missing |
|---|---|

<If none: say the documents were right and the code was wrong. That is the good
case and worth recording.>
```

---

## `bugs/INDEX.md`

```markdown
# Bugs

| ID | What goes wrong | Severity | Status | Feature | Branch |
|---|---|---|---|---|---|
| BUG-1 | | Major | Open | PROJ-7 | - |

Next free ID: BUG-2
```

Bug lifecycle rungs move forward once, the same as the feature board:

| Status | Means | Set by |
|---|---|---|
| `Open` | Reported, nobody has reproduced it | whoever reports it |
| `Reproduced` | A command fails on it today | `/fix`, once the loop is red |
| `Fixed` | Fixed on its branch, regression test green, pull request open | `/fix` |
| `Closed` | Merged into the target | `/merge` |
| `Not reproducible` | The loop could not be built - what was tried is in the bug file | `/fix` |
| `Not a bug` | Behaves as specified, with the document named | `/fix` |

The board is edited in the default branch's checkout, never in the fix worktree:
a status that travels with the branch is invisible until the branch merges.
