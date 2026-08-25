# PROJ-3: Customer profile - Test report

**Tested:** 2026-08-22 · **Branch:** `feature/PROJ-3-customer-profile`
**Environment:** local, Postgres 18 in a container, seeded with the spec's example data

## Verdict

**Not production ready**

Decided by F-1: the confidence dot says the opposite of what the value is. A saved
estimate carries the *confirmed* dot, an empty field carries the *estimated* one.
No test catches it - inverting the flag on purpose leaves all 205 unit and 72
browser tests green.

| Severity | Count |
|---|---|
| Critical | 0 |
| Major | 1 |
| Minor | 2 |
| Cosmetic | 1 |

## Findings
### F-1 - The confidence dot shows the opposite of what the value is · **Major**
### F-2 - Focus is lost after every successful save · **Minor**
### F-3 - With the database stopped the error surface stands outside the shell · **Minor**
### F-4 - Four primary actions on the profile page · **Cosmetic**

---

## Bearbeitet von `/build` am 2026-08-22

| Finding | Done | Commit |
|---|---|---|
| F-1 · confidence dot inverted | Code - the variant follows the origin, not the filled field; E2E asserts the ring | `d4e5f6a` |
| F-2 · focus lost after save | Code - `useFocusReturn()` in all five forms | `f7a8b9c` |
| F-3 · error surface outside the shell | Document - AC-39 names both cases and rules out a shell without a database | `a9b8c7d` |
| F-4 · four primary actions | **open** - a question for docs/design-system.md, recorded in spec.md §Open questions | `b2c3d4e` |

---

## Verdict

**Not production ready**

Decided by F-1: the sector error of the create form never reaches assistive
technology. Everything from the round before holds - the dot follows the origin,
focus returns to the button, the error surface stands inside the shell.

| Severity | Count |
|---|---|
| Critical | 0 |
| Major | 1 |
| Minor | 2 |
| Cosmetic | 1 (carried over from round one, recorded as a question) |

## Findings
### F-1 - The sector error of the create form never reaches assistive technology · **Major**
### F-2 - The toast's live region is created together with its text · **Minor**
### F-3 - Free text with markup is not shown in the row · **Minor**
### F-4 - Four primary actions on the profile page · **Cosmetic**

## The round before, re-measured

| Finding | Result | How it was checked |
|---|---|---|
| **F-1** confidence dot inverted | **fixed** | Measured on the rendered element: `warm` plus a 3px ring on the saved estimate, `ok` on a confirmed value |
| **F-2** focus lost after save | **fixed** | Triggered with the keyboard and re-measured: Save → BODY → Save, ending on Save |
| **F-3** error surface outside the shell | **resolved** | AC-39 now names both cases; both measured, container stopped and API failing |
| **F-4** four primary actions | **open** | Still the same question, still recorded in spec.md |
