# Audit Template

Written to `docs/audits/YYYY-MM-DD.md`. Headings shown in English - write them in
the project's language.

---

```markdown
# Audit - YYYY-MM-DD

**Against:** docs/architecture.md (<version or last change date>) and the plan documents
**Scope:** <whole repository | area>
**State:** <n> features `Done`, <n> in flight, <n> waves built

## In one paragraph
<What the repository looks like against its own rules. Honest, short. If it is in
good shape, say so - an audit that always finds a crisis stops being read.>

| | Repair the code | Ratify the drift | Accept |
|---|---|---|---|
| Findings | | | |

## Findings
### A-1 - <title> · <cost: high | medium | low>
- **Rule:** <which rule in architecture.md or which promise in a plan document>
- **Where:** `path:line`, and <how many other places>
- **Since:** <commit, date - from git log>
- **What it costs:** <concretely, in this product>
- **Proposal:** Repair the code | Ratify the drift | Accept
  - repair → <the smallest change, and where it belongs>
  - ratify → <which section of architecture.md to change, and to what>
- **Filed as:** PROJ-y | BUG-n | not filed, because <…>

## Tenant isolation
| Path to tenant data | Goes through the enforced place | Note |
|---|---|---|

<Enumerated, not sampled. This is the table the audit exists for.>

## Rules decided but not configured
| Rule in architecture.md | Tooling present | Runs in the gate |
|---|---|---|

## Plan truth
| Document | Says | Reality | Which is wrong |
|---|---|---|---|

## Suppressions
| Where | Kind | Reason given | Age | Still valid |
|---|---|---|---|---|

**Total:** <n>, of which <n> without a reason.

## Coverage
- **Floor:** <n>%   **Actual:** <n>%   **Floor last raised:** <date, or "never">
- **Criteria without a test:** <list, or "none">

## The tail
<What was found but not worth listing individually: how many, of what kind, and
whether it is one pattern or noise.>

## Not checked
| What | Why | Risk of leaving it |
|---|---|---|
```
