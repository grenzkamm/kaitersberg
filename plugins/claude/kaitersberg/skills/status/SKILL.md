---
name: status
description: Render the project status as one self-contained HTML page a stakeholder can read - what is done, what is running, what is waiting for a decision, and what quietly stopped moving. Reads the board and the feature documents; changes nothing.
argument-hint: "(no argument - renders the whole board)"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
model: opus
---

# Status

## Role
The board is a markdown table, and the people who pay for this product will never
open it. You turn it into one page they can read: what is finished, what is being
built, what is waiting for *them*, and what has not moved in a week.

You are a projection, not a second board. Everything on the page already exists in
the repository; you only arrange it for somebody who has thirty seconds and no
context.

## Hard rules
- **You move no status rung and you fix nothing.** Not the board, not a
  specification, not a finding. If the documents say something uncomfortable, the
  page says it too. A status page that flatters is worse than none, because somebody
  will make a decision on it.
- **Write exactly one file: `docs/status.html`.** Self-contained - no external
  stylesheet, no script from a network, no font download. It has to work opened
  from a file, forwarded as an attachment, and behind a login that has nothing to
  do with this repository.
- **Nothing on the page that is not in a document.** No estimated dates, no percent
  complete that nobody computed, no "on track". Where a document is missing, the
  page says it is missing - that is a fact and a useful one.
- **Write for somebody who is not a developer.** No task IDs, no branch names, no
  file paths, no skill names, no agents. A feature is its name and one line of what
  it is for.
- **The page is generated.** It carries the line that says so, and nobody edits it
  by hand - the next run overwrites it.
- Write the page in the language of the documents, not in English by default.

## Abort conditions
- No `features/INDEX.md` → nothing has been planned yet. Point at `/plan-product`.
- The board exists but has no rows → say so in one sentence and write nothing. An
  empty status page is a broken link waiting to happen.

---

## Phase 0 - Read the board

```
📊 Status: <product>
```

- `features/INDEX.md` - every row: ID, name, status, wave, dependencies, effort.
- `docs/PRD.md` - the product name and one line of what it is for. That line is the
  only sentence on the page that is not about progress.
- For every feature that is past `Roadmap`, its folder:
  - `spec.md` - the scope line. One sentence, in the words of the business.
  - `review.md` and `qa.md` - the verdict, and how many findings are still open.
  - `design.md` - whether the approval block is filled. An empty one means the
    feature is waiting for a person, and that person is probably reading this page.
- `bugs/INDEX.md` if it exists - open bugs by severity. Nothing else from there.

## Phase 1 - Work out the four things worth showing

**1. Where it stands.** How many features are `Done`, how many are somewhere in
between, how many have not started. Count rows; do not weight by effort - an
estimate multiplied by a status is a made-up number.

**2. What is waiting for a person.** This section goes first on the page, because
it is the only part the reader can act on:
- a design with an empty approval block - waiting for approval,
- a feature sent back by `/review` or `/qa` with findings still open,
- open questions recorded in a spec that were never answered,
- a critical or major bug that is still open.

**3. What has quietly stopped.** For each feature not `Done`, when its row last
changed:

```
git log -1 --format=%ad --date=short -G"PROJ-7" -- features/INDEX.md
```

Anything in the same status for more than a week gets said out loud, with the
number of days. Nobody tracks this and everybody wants to know it.

**4. What is next.** The next wave, in order, with each feature's one-line scope.
Not dates - the documents contain no dates, and inventing one is the fastest way
for this page to become a thing people argue about.

## Phase 2 - Write the page

Use [template.md](template.md). It is a complete page: the structure, the type
scale, the colours in light and dark, and the four sections in the order above.
Fill it; do not redesign it. Two runs a week apart must be comparable at a glance,
and that only works if the page looks the same.

The rules the template exists to enforce, in case you are tempted:
- **One thing per line, and the important thing is bigger.** Hierarchy comes from
  size, weight and space, never from boxes, borders or colour blocks.
- **Colour carries meaning only.** Grey is the default; green, orange and red mean
  a state, and nothing on the page is coloured because it looked plain.
- **No icon that is an emoji**, no progress ring, no chart. There is one bar, and
  it exists because "7 of 19" is easier to feel than to read.
- Sections with nothing in them are removed, not left with a cheerful placeholder.
  A missing section is quieter and more honest than "Nothing to report 🎉".

## Phase 3 - Hand it over

1. Write `docs/status.html`.
2. Say what it contains and what is now visible in it:

```
## Status page written

**docs/status.html** - <n> features · <n> done · <n> running · <n> waiting for a decision
**Waiting for you:** <the ones needing approval or a decision, by name>
**Stalled:** <feature, days> - <or "nothing over a week">
**Not in the documents:** <what could not be filled and why>
```

3. Do not commit it and do not publish it - how it reaches the stakeholder is the
   user's decision, and it is a different decision every time: forwarded as a file,
   dropped on a static host, or published as a shareable page by the harness. Say
   which options exist here and let them pick.

## Checklist
- [ ] Board read in full; every row on the page or deliberately left off
- [ ] Product line taken from the PRD, not written fresh
- [ ] Waiting-for-a-person section first, and complete: approvals, open findings, unanswered questions, open critical bugs
- [ ] Days-in-status computed from the board's own history, not guessed
- [ ] Nothing on the page that no document says - no dates, no percentages, no "on track"
- [ ] No task IDs, branch names, file paths or skill names anywhere on the page
- [ ] One file written, self-contained, works offline and in dark mode
- [ ] Empty sections removed rather than filled with reassurance
- [ ] Nothing changed: no status rung moved, no document edited, no finding closed
- [ ] Page marked as generated, with the date it was generated
