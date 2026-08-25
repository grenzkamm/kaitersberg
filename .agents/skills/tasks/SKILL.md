---
name: tasks
description: Break one feature's specification and technical design into an ordered task list for implementation - grouped by layer, dependency-ordered, every task traceable to an acceptance criterion and verifiable on its own. The bridge between design and code. Writes no code.
---
<!-- Generated from .claude/skills/tasks/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Tasks

## Role
You turn one approved design into the list somebody works through. This is the
last document before code, and the one that decides whether the implementation
matches what was approved - or quietly drifts.

Two properties make or break the list:

1. **Every acceptance criterion is covered by a task, and every task serves an
   acceptance criterion.** Both directions. An AC with no task never gets built;
   a task with no AC is work nobody asked for.
2. **Every task ends in a state that can be checked.** Not "started on the form" -
   a task is done when something is true that was not true before, and somebody can
   see that it is true.

## Hard rules
- **No code.** Task descriptions, not implementations.
- **No "write the tests" task.** The test that proves an AC belongs to the task
  that implements that AC. A separate testing task at the end is how test debt is
  created on purpose.
- **No "refactor afterwards" task, no "polish later" task.** If it is needed, it is
  part of the task that creates the need. If it is not needed, it is not a task.
- **No task named after a file or a layer alone.** "Add the controller" is an
  activity. "A client can be created with an address" is an outcome.
- **A task fits in one sitting.** Roughly half a day. Bigger than that means it is
  two tasks, and you have not found the seam yet.
- The list is written in the language of the specification.

## Abort conditions
- No `design.md` for this feature, or its approval block is empty → the design is
  not approved and the tasks would be based on a draft. Say so and stop.
- The design has entries under *To decide* → list them; a task list built over an
  open decision produces rework in exactly that spot.

---

## Phase 0 - Pick the feature

```
🧱 Tasks: PROJ-x [name]
```

With an argument, take that ID. Without, take the first feature whose folder has an
approved `design.md` but no `tasks.md`.

## Phase 1 - Read and inventory

Read `spec.md` and `design.md` in full, plus `docs/architecture.md` if it exists
and the plan documents the design refers to.

Write yourself two lists before cutting anything:
- **Every `AC-n`** from the spec, with its test level.
- **Everything the design promises**: each field, each role rule, each component,
  each route, each setting, each environment variable, each dependency, each
  abuse-protection check, each personal-data obligation, **each migration step with
  its backfill**, and **the non-functional numbers** from the spec - the performance
  budget for this feature's path and the volume it must hold.

Both lists must end up consumed by tasks. Nothing from either may quietly vanish.

## Phase 2 - Cut the tasks by layer

Group by layer, because that is how the work is picked up - but **order by
dependency**, not by layer. A UI task whose data exists can start before the last
data task is finished.

| Layer | Holds |
|---|---|
| **Data** | Schema change, migration, backfill of existing rows, status values, the fields exactly as the design lists them |
| **Rules** | Validation, calculation, invariants, anything that must hold no matter who calls it. This is where the business logic lives, not in the interface |
| **Interfaces** | The operations the outside world can perform, with the permission check on each one - the admin/user difference from the design becomes real here |
| **Interface surface** | Components, pages, routes, states - reused ones wired up, new ones built as the design's component tree says; each E2E criterion leaves an executable browser test in the project-owned suite |
| **Protection** | Abuse limits, tenant isolation checks, hostile input handling, and the personal-data obligations: retention, erasure, export |
| **Finishing** | Empty, loading and error states, the exact texts, formats, supported viewports, keyboard path and focus order, accessibility semantics, performance against the number in the spec |
| **Closing** | Environment variables and configuration landed, plan documents corrected, migration verified against real data |

**Protection and Finishing are not optional and are not "later".** They are the two
layers a rushed feature drops, and they are the two that the spec made mandatory.
If a task list ends at Interface surface, it is incomplete.

**Every task carries:**
- an ID `PROJ-x-T<n>` and a title stating the outcome,
- the layer,
- the ACs it satisfies,
- the tasks it depends on,
- **writes**: the files or modules this task creates or changes - its exclusive
  claim while it runs,
- **reads**: what it needs but does not change,
- **brief**: which sections of `spec.md` and `design.md` somebody needs to do this
  task without having read anything else,
- **done when**: the observable condition, including which test now passes,
- for an E2E criterion, the browser project(s) from the UI test contract, the named
  fixture/reset path and the executable test that passes - never a later QA-only test,
- a size: S (an hour or two), M (half a day). There is no L - split it.
- an **executor**: `worker` for an isolated task, `orchestrator` for shared state.
  A task that writes a lockfile, migration sequence, shared application shell,
  navigation, configuration or plan document is always `orchestrator`; put it in a
  singleton batch. `$build` cannot safely dispatch shared state to a worker merely
  because no sibling happens to name the same file today.

## Phase 3 - Order it into batches

The list is executed by an agent that will hand each batch to sub-agents working at
the same time. So parallelism is not a hint in prose - it is a decision written per
task, and the file has to be safe to act on without further thought.

- Dependencies point backwards only.
- **Name the first point where something works end to end**, however crudely, and
  order the early tasks to reach it. A list that only becomes visible at task 14
  hides its own mistakes for two days.
- A task that unblocks many others goes early even when it is small.

**Group the tasks into numbered batches.** A batch is what one round of sub-agents
does at the same time. Two tasks belong in the same batch only when **all** of
these hold:

1. Neither depends on the other, and both their dependencies are in earlier batches.
2. **Their write sets are disjoint.** Not "probably fine" - compare the lists.
   Reading the same file is fine; two agents writing it is a lost edit.
3. Neither needs the other's result to know what to build.

**Never put in the same batch**, regardless of how independent they look:
- two tasks that change the database schema or add migrations - order matters and
  the migration sequence is shared state,
- two tasks that add dependencies - the lockfile is one file,
- two tasks that touch the shared application shell, the navigation, or the same
  configuration file,
- two tasks that correct the same plan document.

Where such a collision is unavoidable, split the shared part into its own earlier
task and let both depend on it. That is almost always possible and always better
than serializing two large tasks.

**Every batch ends at a gate**: what must be true before the next batch starts -
tests green, migration applied, the application still starts. A batch whose gate
fails does not hand off; it gets fixed first.

Use a **batch gate**, not the whole repository gate by reflex: the new and affected
tests, formatting/lint/types for the touched scope, and the smallest smoke path that
proves integration. The full architecture gate runs once after the target branch is
brought into the finished feature. Re-running every browser project after every
batch makes batch count the dominant cost without increasing the independence of
the final proof.

**Each task must be self-contained enough to hand over.** The sub-agent that picks
it up has not read the spec, the design, or this conversation. Its *brief* names
the sections it must read, the ACs it must satisfy, and the tests that must pass.
If a task cannot be described that way, it is entangled with another one - merge
them or find the seam.

## Phase 4 - Check the coverage both ways

- **AC → task**: every `AC-n` appears in at least one task. A missing one is either
  a forgotten task or an AC that should not have survived the spec.
- **Task → AC**: every task names at least one AC. A task that cannot is either
  enabling work - migration, configuration, wiring - which is allowed but must say
  so, or it is scope creep, which is not.
- **Design → task**: walk the design's inventory from Phase 1. Each field, route,
  component, setting, variable, dependency and protection check appears somewhere.

Report anything the checks turn up rather than silently patching it - a gap here
usually means the spec or the design has a hole, and that hole belongs upstream.

## Phase 5 - Validate the executable cut

Present the list grouped by layer: IDs, titles, sizes, executors, and the first
end-to-end point, plus anything the coverage check found. Ask before writing only
when the task cut changes approved behaviour, exposes a design gap, or exceeds the
review budget: by default more than 10 tasks or 5 sequential batches. Otherwise the
approved design already supplies the authority to write the mechanical breakdown.

## Phase 6 - Write and hand off

1. Write `features/PROJ-x-<name>/tasks.md` from [template.md](template.md).
2. `features/INDEX.md`: status `Designed` → **`Ready`**. That is the signal that
   `$build` may claim this feature. The implementer sets `In Progress` when it does.
3. Report:

```
## PROJ-x - [name], N tasks

Data D · Rules R · Interfaces I · Surface S · Protection P · Finishing F · Closing C
**Works end to end after:** PROJ-x-T<n>
**Batches:** B1 (1 task) → B2 (3 parallel) → B3 (2 parallel) → B4 (1 task)
**Widest batch:** <n> tasks at once
**Coverage:** all M ACs covered · <or: AC-k has no task, because …>

Next: `$build PROJ-x`, starting at PROJ-x-T1.
```

4. Commit: `docs(PROJ-x): Add task breakdown for [name]`

## Checklist
- [ ] Design read and approved, open decisions none or listed
- [ ] Every AC of the spec covered by at least one task
- [ ] Every task names at least one AC, or declares itself enabling work
- [ ] Every field, route, component, setting, variable, dependency and migration step of the design consumed
- [ ] The spec's performance number and volume have a Finishing task that checks them
- [ ] Protection and Finishing layers present, not deferred
- [ ] Every task has an observable "done when", including the test that passes
- [ ] No task larger than half a day, no test-only task, no refactor-later task
- [ ] Dependencies point backwards only
- [ ] First end-to-end point named
- [ ] Every task lists what it writes, what it only reads, and worker or orchestrator execution
- [ ] Shared-state tasks are orchestrator-owned singleton batches
- [ ] Batches numbered; within each batch the write sets are disjoint, checked list against list
- [ ] No batch contains two schema changes, two dependency additions, or two edits of one shared file
- [ ] Every batch has a targeted gate; the full repository gate is reserved for the integrated feature
- [ ] Every task's brief names the sections and ACs a sub-agent needs, and nothing else
- [ ] User approved only task cuts that changed behaviour, exposed a design gap or exceeded the review budget
- [ ] `features/INDEX.md` set to `Ready`
