# PROJ-3: Customer profile - Review

**Verdict:** Changes required
**Against:** spec.md, design.md (approved 2026-08-21) · **Diff:** 41 files, +1.980 / −64

One finding decides it. The rest are notes.

## Findings
### F-1 - The backfill writes a timestamp the application can never store again
### F-2 - `toAddress` promises a row type that holds less than it reads

## Notes
### A-1 - The region field shows the previous value until the page is reloaded
### A-2 - docs/architecture.md still documents the old update signature

---

## Bearbeitet von `/build` am 2026-08-22

| Finding | Done | Commit |
|---|---|---|
| F-1 · backfill timestamp | Code - the migration truncates to milliseconds; regression test runs the real backfill | `a1b2c3d` |
| F-2 · toAddress row type | Code - the type names every column it reads | `e4f5a6b` |
| A-1 · region field stale | Code - the form reads back what the server returned | `b7c8d9e` |
| A-2 · architecture signature | Document - the section describes the signature that exists | `c1d2e3f` |

---

## Verdict: **Approved with notes**

Two notes, neither blocking. Nothing does what must not happen: no data loss, no
hole in the tenant isolation, no personal data in the wrong place.

## Notes
### N-1 - `normalizeName` has no caller except its own test
### N-2 - The origin list is written twice, once in shared and once in the fixture
