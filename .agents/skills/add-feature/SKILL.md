---
name: add-feature
description: Put a feature request that arrived after planning onto the board - deciding first whether it is one, then where it belongs, what it costs the waves already planned, which plan documents it changes, and whether it makes an approved design stale. Plans only; writes no code.
---
<!-- Generated from .claude/skills/add-feature/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Add Feature

## Role
Something was forgotten, or something changed. You put it on the board honestly:
in the right place, with its true cost to everything already planned, and with the
plan documents corrected - rather than as a row appended at the end that everybody
will discover is urgent three waves too late.

The temptation here is to say yes cheaply. A feature added without recomputing what
it displaces is how a six-wave plan silently becomes a nine-wave plan.

## Hard rules
- **Never renumber.** A new feature takes the next free `PROJ-n`, even if it belongs
  in wave 1. The ID is identity, not order; renumbering breaks every branch, commit
  message, test name and document that already cites one.
- **Priority still follows dependencies, not urgency.** "We need it for the launch"
  sets the wave, never the priority. Those are two different questions and mixing
  them is how P0 stops meaning anything.
- **Say what it displaces, in features.** Inserting into a wave pushes the ones
  after it. Name which, and offer what could come out to keep the date. Days are a
  guess; features are countable.
- **Correct the plan in the same pass.** New entities, roles, limits, routes or
  variables change `data-model.md`, `access.md`, `app-shell.md`, `local-dev.md`. A
  feature added to the board over a plan that does not know about it is a trap for
  whoever specs it.
- **No code, no spec.** This puts it on the board. `$write-spec` writes it when it
  is next.

## Abort conditions
- No `features/INDEX.md` → nothing was planned. Point at `$plan-product`.

---

## Phase 0 - Is it actually a new feature?

```
➕ Request: <what was asked for>
```

Four things arrive looking the same. Decide which this is, out loud, before
anything else:

| It is | When | Where it goes instead |
|---|---|---|
| **A change to an existing feature** | It alters what a feature on the board already does | Its scope line - and if that feature has a spec or an approved design, a revision there, which is a decision the approver must see |
| **A bug** | The product already promises this and does not do it | `$fix` |
| **Scope creep** | Nobody asked for it, it just occurred to somebody | `docs/PRD.md` non-goals, with the reason. Writing it down is not a rejection; it stops it being re-proposed monthly |
| **A new feature** | The product does not promise it, and should | Continue here |

If it is a new feature and the product was supposed to be finished without it,
**that is worth saying**: the non-goals list, or the journeys, or the target users
were wrong. Which one, and how wrong, tells you whether this is a single oversight
or the first of several.

## Phase 1 - Understand it, briefly

Ask only what changes its placement (a multiple-choice question, recommendation first):

- Who needs it, from `docs/access.md` - a role that does not exist yet is a much
  larger request than a feature.
- What it depends on: which entity, which screen, which existing feature.
- What depends on it: is anything already on the board waiting for this without
  saying so?
- **Is it needed for the first release, or after?** This sets the wave and nothing
  else.

## Phase 2 - Place it

1. **Next free `PROJ-n`** from the board.
2. **Scope line**: what is in it, and the nearest thing deliberately not - same
   discipline as every other row.
3. **Priority** from dependencies: P0 only if something else cannot exist without
   it.
4. **Size** S / M / L, and if L, cut it in two now rather than at build time.
5. **Dependencies**, both directions. Check every existing row for one that
   silently assumed this feature existed.
6. **Wave**:
   - *Needed for the first release* → the earliest wave whose dependencies it
     satisfies. Then check that wave's **parallel safety**: does it share a surface
     - the app shell, an entity's schema, a route - with something already there? If
     yes, either split the shared part out or serialize, and update the parallel
     table.
   - *After the first release* → a wave after the release cut. Low ceremony; a row,
     a scope line, done.

## Phase 3 - Say what it costs

Not optional, and not softened:

```
PROJ-n lands in wave <w>.
Pushed back: <the features that now come later, by name>
Also affected: <features whose dependencies changed>
To keep the original scope of wave <w>: <what would have to come out, or move>
```

If it is needed for the first release and something in flight is affected, say
which and how badly:

- a feature at `Spec` or `Designed` → its document needs revisiting before it is
  built; name the section,
- a feature `In Progress` → **stop and consider pausing that build**. Finishing
  against a design that is now stale costs more than the pause, and the person
  building it cannot see this from inside their worktree,
- a feature at `In Review` → usually finish it; note the follow-up.

Then let the user choose: take the cost, cut something, or push the new feature
past the release.

## Phase 4 - Write it down

1. `features/INDEX.md`: the row, the scope line, the build order text for its wave,
   the parallel-safety table, the next free ID.
2. `docs/PRD.md`: the roadmap table, and - if this exposed a wrong assumption - the
   non-goals or the target users, with a line saying what changed and why.
3. The plan documents it touches: `data-model.md` for new entities or fields,
   `access.md` for roles, permissions or limits, `app-shell.md` for routes and
   navigation, `local-dev.md` for new variables or services.
4. Any existing feature whose scope line, dependencies or wave changed.
5. Report:

```
## PROJ-n - <name>

**Placed:** wave <w>, <prio>, <size>, depends on <…>
**Because:** <what forced this wave>
**Cost:** <what moved, by name>
**In flight:** <what is affected and what you should do about it - or "nothing">
**Plan corrected:** <which documents>
**This request revealed:** <the wrong assumption, or "nothing - it is simply new">

Next: `$write-spec PROJ-n` when it comes up in the order.
```

6. Commit: `docs(PROJ-n): Add feature to the roadmap`

## Checklist
- [ ] Decided out loud whether this is a feature, a change, a bug or scope creep
- [ ] Next free ID used; nothing renumbered
- [ ] Priority from dependencies, wave from the release need - kept apart
- [ ] Dependencies checked in both directions against every existing row
- [ ] Parallel safety of the target wave rechecked, shared surfaces named
- [ ] Displacement stated by name, with an option to keep the original scope
- [ ] Effect on work in flight stated, including whether a build should pause
- [ ] Plan documents corrected in the same pass
- [ ] If the request exposed a wrong assumption, it is written into the PRD
- [ ] No specification, no code
