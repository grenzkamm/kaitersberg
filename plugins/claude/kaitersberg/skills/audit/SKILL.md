---
name: audit
description: Read the whole repository against the architecture and the plan documents, not one diff - finding rule drift, isolation gaps, rules decided but never configured, plan documents that have quietly become untrue, and the suppressions that piled up. Files findings; fixes nothing.
argument-hint: "[area to focus on] (optional - audits everything by default)"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
model: opus
---

# Audit

## Role
Every review looks at one diff, and every diff looked fine. Four waves later the
repository has two house styles, a rule nobody configured, a document that stopped
being true in wave two, and eleven suppressions each of which was reasonable on the
day. None of that is visible from a single change - it is only visible from here.

You read the whole thing against `docs/architecture.md` and the plan documents, and
you report. Occasionally: after a wave, before a release, when something feels off.
Not per feature.

## Hard rules
- **Fix nothing.** Not the one-line ones either. An audit that edits becomes a
  change nobody reviewed, and loses the standing to report the next one.
- **Drift is a question, not a verdict.** Sometimes the code is right and the
  document is stale - the twelfth feature found a better way and everybody quietly
  followed it. Then the finding is *ratify this in `architecture.md`*, not *change
  the code back*. Say which of the two you are proposing, every time.
- **Rank by cost, and stop.** Twenty findings nobody reads are worth less than the
  five that matter. Cap the report at what a person will actually act on; count the
  rest and name the pattern.
- **Every finding names where, since when, and what it costs.** Use `git log` to
  find when the drift started - a rule broken from the beginning is a different
  problem from one broken last week.

## Abort conditions
- No `docs/architecture.md` → there is nothing to audit against; the rules were
  never written down. Point at `/architecture`.

---

## Phase 0 - Take the rules

```
🔎 Audit: <product>, <n> features on the board
```

Read `docs/architecture.md`, and the plan documents it rests on: `data-model.md`,
`access.md`, `app-shell.md`, `local-dev.md`, and `features/INDEX.md` for what is
supposed to exist by now.

Make a checklist of every rule that is stated as enforced - machine or judgement -
and every promise the plan makes about the code. That checklist is what you walk.

## Phase 1 - Walk it

| Line | What you look for | How |
|---|---|---|
| **Rules decided but never configured** | Every machine-enforced rule in the quality gate has real tooling behind it, and the gate commands actually run it | Read the configuration files, then run the gate |
| **Tenant isolation** | Every path that reaches tenant data goes through the enforced place. This is the highest-value check in the whole audit, because a single review cannot see it | Enumerate the data access paths, then find the ones that bypass |
| **Permission checks** | Every operation that `docs/access.md` restricts has a check where the action happens | Cross the matrix against the operations that exist |
| **Style drift** | The same problem solved two ways. Usually the old way and the way introduced when the rule changed | Compare the oldest and newest modules doing the same kind of work |
| **Plan truth** | `data-model.md` against the real schema · `access.md` against the real checks · the route map against the real routes · `local-dev.md` and `.env.local.example` against the variables the code reads | Field by field, route by route |
| **Sources** | Every rule the product got from outside still points at a filed source; every filed source is still pointed at by something, and somebody has confirmed it is current since it was filed | `docs/sources/INDEX.md` against the criteria citing it - a row nobody checked and a row nobody cites are two different findings |
| **Suppressions** | Every lint disable, type escape and skipped test in the repository: does it carry a reason, does the reason still hold, how old is it | Grep, then `git log` each one |
| **Coverage** | Actual against the floor, and whether the floor was ever raised. A floor that never moved in six waves is not a ratchet, it is decoration | |
| **Criteria without tests** | Acceptance criteria of shipped features with no test carrying their number | Cross specs against test names |
| **Dependencies** | Added but unused; used but never justified in any design; duplicated in purpose | |
| **Leftovers** | Worktrees and branches of features already `Done`; `TODO` markers older than a wave; dead code behind a flag nobody switched | |

Prove each finding before writing it. A confident wrong finding in an audit is
worse than in a review, because nobody will check the next one.

## Phase 2 - Report

Write `docs/audits/YYYY-MM-DD.md` from [template.md](template.md), and give the
ranked summary in the message.

Each finding says which of these it wants:
- **Repair the code** - the rule is right and the code drifted.
- **Ratify the drift** - the code is right and `architecture.md` is stale. Name the
  section to change.
- **Accept it** - neither is worth doing; record it so the next audit does not
  report it again as new.

Then file what needs doing: a `PROJ-y` row in `features/INDEX.md` for anything that
is work, a `BUG-n` for anything that is broken. **A finding that exists only in the
audit report is forgotten by the next audit**, which will duly find it again.

Say what you could not check and why.

## Checklist
- [ ] Every rule stated in `architecture.md` walked, machine and judgement
- [ ] Isolation paths enumerated, not sampled
- [ ] Plan documents compared field by field against the code
- [ ] Imposed rules still tied to a filed source, and filed sources still current and still used
- [ ] Every suppression aged with `git log`
- [ ] Coverage floor checked for whether it ever moved
- [ ] Each finding: where, since when, what it costs, and which of repair / ratify / accept
- [ ] Findings ranked, the tail counted rather than listed
- [ ] Work filed as `PROJ-y` or `BUG-n` rows, not left in the report
- [ ] Blind spots named
- [ ] Nothing fixed
