# Tasks Template

Written to `features/PROJ-x-<short-name>/tasks.md`, beside `spec.md` and
`design.md`. Headings shown in English - write them in the language of the
specification.

---

```markdown
# PROJ-x: <Feature name> - Tasks

**Based on:** [spec.md](spec.md) · [design.md](design.md)
**Created:** YYYY-MM-DD
**Works end to end after:** PROJ-x-T<n>

## Order at a glance
| # | Task | Layer | Batch | Executor | Size | Depends on | ACs | Writes | Status | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| PROJ-x-T1 | <outcome, not activity> | Data | B1 | orchestrator | S | - | AC-1 | <its exclusive files> | Open | - |

Status runs `Open` → `In Progress` → `Done`. Claiming means setting owner and
status in one edit, before starting.

## Batches
One batch = one round of parallel work. Within a batch the write sets are
disjoint, so the tasks can be handed to sub-agents at the same time. Do not start
a batch before the previous gate holds.

| Batch | Tasks | Runs at once | Targeted gate before the next batch |
|---|---|---|---|
| B1 | T1 | 1 | `<affected commands from the architecture's batch recipe>` - migration applied, application starts |
| B2 | T3, T4, T5 | 3 | `<affected commands>` - tests of AC-3…AC-5 green |

**Checked disjoint:**
| Batch | Task | Writes | Overlap with siblings |
|---|---|---|---|
| B2 | T3 | <files> | none |
| B2 | T4 | <files> | none |

**Deliberately not parallel:** <which tasks were kept apart and why - schema
order, one lockfile, the shared shell>

## Integrated feature gate

`<the exact complete command sequence from docs/architecture.md>`

Run once after the target branch is integrated into the finished feature, never in
a batch row. Every batch row above was compared with this command and does not
invoke or delegate to it.

---

## Data

### PROJ-x-T1 - <outcome>
**Covers:** AC-1, AC-2   **Size:** S   **Batch:** B1   **Executor:** orchestrator   **Depends on:** -
**Writes:** <the files or modules this task owns while it runs>
**Reads:** <what it needs unchanged>
**Brief for whoever picks this up:** read `spec.md` §Data and §AC-1…AC-2,
`design.md` §Data. Nothing else is needed.

<Two or three sentences: what exists afterwards. Fields exactly as design.md
lists them - do not restate the table, point at it.>
**Done when:** <observable condition> · test `AC-1 <short title>` passes.

## Rules

### PROJ-x-T2 - <outcome>
**Covers:** AC-3   **Size:** S   **Batch:** B2   **Executor:** worker   **Depends on:** T1
**Writes:** … **Reads:** … **Brief:** …
**Done when:** …

## Interfaces

### PROJ-x-T3 - <outcome>
**Covers:** AC-4, AC-7 (permission)   **Size:** M   **Batch:** B2   **Depends on:** T1, T2
**Writes:** … **Reads:** … **Brief:** …
**Done when:** … · the refused role gets refused, test `AC-7 …` passes.

## Interface surface

### PROJ-x-T4 - <outcome>
**Covers:** AC-5   **Size:** M   **Batch:** B3   **Depends on:** T3
**Writes:** … **Reads:** … **Brief:** …
**Reuses:** <components from design.md marked reused>
**Done when:** … · project-owned browser test `<AC-5 …>` passes for
<required projects from the UI test contract> using <named fixture/reset path>.

## Protection

### PROJ-x-T5 - <outcome>
**Covers:** AC-8 (tenant isolation), AC-9 (limit)   **Size:** S   **Batch:** B3   **Depends on:** T3
**Writes:** … **Reads:** … **Brief:** …
**Done when:** <the limit holds at its number> · <what is recorded>.

### PROJ-x-T6 - <personal-data obligation from the spec>
**Covers:** AC-10 (erasure), AC-11 (export)   **Size:** S   **Batch:** B3   **Depends on:** T1
**Writes:** … **Reads:** … **Brief:** …
**Done when:** …

## Finishing

### PROJ-x-T7 - <outcome>
**Covers:** AC-6 (empty state)   **Size:** S   **Batch:** B4   **Depends on:** T4
**Writes:** … **Reads:** … **Brief:** …
**Done when:** empty, loading and error states match the app shell · texts match
the spec's text table · the flow is reachable by keyboard · focus lands where the
spec says · accessible roles and names expose the controls · required viewports
remain usable.

## Closing

### PROJ-x-T8 - <outcome>
**Enabling work** - no AC   **Size:** S   **Batch:** B4   **Depends on:** T1
**Writes:** … **Reads:** … **Brief:** …
**Done when:** environment variables in `.env.local.example` and
`docs/local-dev.md` · plan documents corrected as design.md listed · migration run
against a copy of real data without loss.

---

## Coverage
| AC | Task |
|---|---|
| AC-1 | T1 |

| Task | AC | Or: why it has none |
|---|---|---|
| T8 | - | Enabling work: configuration and plan correction |

**Gaps found:** <what the coverage check turned up, and where it belongs -
upstream in the spec or the design, not patched here. "None" is the good case.>
```
