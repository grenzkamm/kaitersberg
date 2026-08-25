---
name: scaffold
description: Turn the plan and the architecture into a repository a developer can actually run - folder skeleton, database and services in containers, migrations, test harness, the quality gate configured with its real thresholds, CI, and env examples. Ends by proving the documented commands work from a fresh clone. The one skill allowed to write configuration and start services.
argument-hint: "(no argument - runs once, after /architecture)"
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: opus
---

# Scaffold

## Role
The plan says what is built, the architecture says how. You make the repository
where that can happen: dependencies installed, database running, migrations
working, tests running, the quality gate wired with the numbers it was given.

This is `PROJ-1` - the foundation feature every wave-1 task depends on. It skips the
*specification* half of the pipeline: a container definition has no user stories and
no permission matrix, and writing them would be ceremony. It does not skip the
*delivery* half. You work on your own branch like every other feature, your proof
run is the acceptance, and a fresh `/review` reads the result against the documents
it was built from before `/pr` merges it.

## Hard rules
- **This is the one skill that writes configuration and starts services.** Every
  other skill plans or builds features; this one makes the ground they stand on.
  That is also why **a person starts it and no model calls it by itself**: an agent
  that decides mid-task that some configuration would help has just changed the
  ground under every other feature, and nobody asked it to.
- **No application code beyond a walking skeleton.** One route that answers, one
  smoke test that proves the harness runs, one migration that proves the database
  is reachable. Everything else is a feature and waits its turn.
- **Ports come from `docs/local-dev.md`.** If they are taken, allocate a free range
  and correct the document. **Never stop another project's services.**
- **Never write `.env.local`.** Write `.env.local.example`, then print the values
  the user must paste, in a copyable block.
- **Prove it, do not claim it.** The skill ends with the documented commands run
  from a clean state. A `local-dev.md` that has never been executed is fiction.

## Abort conditions
- No `docs/architecture.md` → the folder layout, the test setup and the quality
  thresholds are not decided yet. Point at `/architecture`.
- The repository already has an application in it → say what is there and ask what
  should be adopted rather than overwritten. Scaffolding over existing work is how
  a day disappears.

---

## Phase 0 - Read the decisions

```
🏗 Scaffold: <product>
```

- `docs/architecture.md` - module layout, naming, migration tooling, test levels
  and their setup, and **the quality gate table with its tools, settings and
  thresholds**. All of it is already decided; you are the one who types it in.
- `docs/local-dev.md` - ports, commands, external accounts, environment variables.
- `docs/PRD.md` - the stack row, hosting and compliance.
- `docs/data-model.md` - enough for the first migration, no more.

Check the ports are actually free (`lsof -i -P -n | grep LISTEN`). Taken means
allocate elsewhere and correct the document - never means stop what is running.

**Claim it and branch, like any other feature.** Set owner and status `In Progress`
on `PROJ-1` in `features/INDEX.md` in one edit, then work on
`feature/PROJ-1-scaffold` in its own worktree - inside Orca (`ORCA_WORKTREE_ID`
set, `orca` on the `PATH`) created through the `orca-cli` skill, otherwise plain
git. The foundation is the one change that
every later feature inherits without reading it; it does not get to be the one that
lands on the main branch unreviewed.

## Phase 1 - The skeleton

In the order that lets you check each step before the next depends on it:

1. **Repository**: package manifest, the folder layout from the architecture, the
   ignore file. Nothing speculative - no folders for features that do not exist.
   **Resolve every version at install time, not from memory.** Ask the registry
   what the current stable release is - `npm view <pkg> version`, the equivalent for
   the ecosystem in use, or the project's own release page - and install that. Never
   an alpha, beta, canary or release candidate. Never a major you remember: an agent
   whose training ended before the last release will reach for `next@14` or
   `tailwindcss@3` with complete confidence, pin it exactly as instructed, and the
   product starts a major behind on day one with a paper trail that makes it look
   deliberate. Where an older line is genuinely required - a peer dependency, the
   hosting runtime, one package that has not caught up - install it and **write the
   reason into `docs/local-dev.md`**, because "old" without a reason is invisible.
   **Then read that version's own documentation before writing any setup step**:
   the frameworks this pipeline meets most often changed exactly that between
   majors - the router and its config, the way the CSS framework is configured, the
   component CLI's name and its commands. Setup written from memory produces a
   repository that installs the new major and configures the old one.
   **Pin every dependency to an exact version** - a range means two developers and
   CI can install three different products - and once they are installed, fill the
   **Stack & versions** table in `docs/local-dev.md` from the lockfile: what
   actually landed, and the link to the documentation *for that version*. Every
   later skill writes and reviews code against that table. A version nobody wrote
   down is a version that gets guessed, and a guessed major is a whole batch of
   plausible code that does not run. **Commit the lockfile.** An ignored lockfile
   makes the pinning above decorative.
2. **Quality gate**: formatter, linter with the chosen rule set, type checking at
   the chosen strictness, coverage reporting with **the floor from the
   architecture**, module boundary rules if any. Wire the exact gate commands the
   architecture named, so `/build` can run them verbatim.
   Then the **git hooks the architecture decided**, if it decided any: versioned in
   the repository and activated by the documented install command. Git's own
   `core.hooksPath` is the default mechanism and needs nothing installed; a hook
   manager is a dependency like any other, so use the one the architecture named and
   expect it to have been justified there under its own dependency policy - if it
   was not, say so rather than installing it quietly. A hook runs only the fast
   subset it was given; the full gate stays where it was. Document in
   `docs/local-dev.md` what activates them and that `--no-verify` bypasses them,
   because a bypass nobody wrote down gets discovered by accident and then used by
   habit.
3. **Services in containers**: the database, and anything else the plan needs
   locally - on the allocated ports, with a volume so data survives a restart, and
   a health check so "it is up" is answerable. Nothing that only production needs.
4. **Migrations**: the tool from the architecture, the naming convention, and one
   real migration creating one entity from the data model. It exists to prove the
   path works, not to model the product.
5. **Test harness**: one test at each level the architecture named, each asserting
   something real. For browser E2E, install and configure the chosen project-owned
   runner, start the application the documented way, and drive one real route
   through the interface. Implement the architecture's projects, isolated state,
   authentication, locator, wait, retry and failure-artefact rules. The database
   fixture is set up the way the architecture says.
6. **Walking skeleton**: the application starts, answers on its port, reaches the
   database. That is all it does.
7. **Seeding**: one documented command that fills a clean database with a
   development tenant set - **at least two tenants and one user per role from
   `docs/access.md`**, with known credentials. Every later skill assumes this
   exists: `/qa` cannot test isolation with one tenant, and the pull request runbook
   tells a reviewer to seed and log in. Features add their own example data on top
   later; you build the mechanism and the tenants.
8. **Environment**: `.env.local.example` with every variable, one comment per line,
   secrets as placeholders, server-side ones marked as such.
9. **CI**: the same gate commands, on the same versions, including browser binaries
   and system dependencies needed by the E2E runner. Say where CI gets what it needs
   to run them: the database as a service container with the same major version as
   local, migrations and seed applied the documented way, and the environment
   variables from `.env.local.example` as repository secrets with test values -
   never a real secret and never a copy of a developer's file. Upload the
   architecture's failure artefacts without uploading successful-run noise. A gate
   that passes locally and is not run on the branch will be broken within a wave.

**Commit as you go, not at the end.** The nine steps are already in the order that
lets each one be checked before the next depends on it, so commit at four points -
after the gate is wired (1–2), after services and migrations run (3–4), after the
harness, the skeleton and the seed prove themselves (5–7), after CI is green (8–9):
`feat(PROJ-1): <what now works>`. One commit holding the whole foundation is the
hardest commit in the project to review and the one nobody can bisect. Never commit
a step that has not run.

Ask only where a decision was genuinely left open, and prefer the boring option.

## Phase 2 - Prove it

From a clean state - a fresh clone or a cleaned tree - run exactly what
`docs/local-dev.md` tells a developer to run, in that order, and record what
happened. Then:

- stop the services and start them again: does the data survive,
- reset the data the documented way: does it come back,
- break one test deliberately: does the gate go red,
- break the browser smoke test deliberately: does its first run go red and leave
  the promised trace, screenshot, console and failed-request evidence,
- check the coverage floor is enforced, not merely reported.

**Every command that did not work the way the document says gets the document
corrected**, not a note in the report. That is the deliverable: `local-dev.md` is
now true.

## Phase 3 - Hand over

1. Correct `docs/local-dev.md` where reality differed, and `docs/architecture.md`
   where a decision turned out impossible as written - with a line saying so.
2. **Write the proof to `features/PROJ-1-scaffold/proof.md`**: every documented
   command with the output it actually produced, the restart and reset results, the
   deliberately broken test and the gate going red, the coverage floor being
   enforced, and what you could not prove. This feature has no `spec.md` and no
   `qa.md`; this file is what `/review` reads its expectation against and what `/pr`
   carries in place of a test report. A proof that lives only in a chat message is
   gone by the time somebody asks.
3. `features/INDEX.md`: `PROJ-1` to `In Review`, owner kept - edited and committed
   in the default branch's checkout, as every board edit is. `Done` is set by `/merge`
   after it merges, exactly as for every other feature - the foundation is not
   finished because it works on your machine.
4. Commit the proof: the document corrections from Phase 2, `proof.md`, and anything
   the clean run exposed - `feat(PROJ-1): Prove the documented commands from a clean
   state`. The foundation itself is already committed in the four steps above.
5. Report:

```
## PROJ-1 - Scaffold

**Runs:** <what starts, on which ports, with which command>
**Gate:** <the commands> - lint ✓ types ✓ tests <n> ✓ coverage <n>% (floor <m>%)
**Proven from clean:** install ✓ · migrate ✓ · seed ✓ · start ✓ · reset ✓ · restart keeps data ✓
**Corrected:** <which documents, and why>

Paste into `.env.local` yourself - I do not write that file:
<the block>

Next: `/review PROJ-1`, in a fresh session - then `/pr PROJ-1` and `/merge PROJ-1`.
`/write-spec PROJ-2` once PROJ-1 is `Done`.
```

## Checklist
- [ ] Ports checked free; nothing else stopped; document corrected if reallocated
- [ ] Folder layout matches the architecture, nothing speculative added
- [ ] Versions resolved from the registry at install time, current stable, no pre-releases; any deliberately older line carries its reason in `docs/local-dev.md`
- [ ] Setup steps written against the installed version's own documentation, not from memory
- [ ] Every dependency pinned exactly, and the installed versions written into `docs/local-dev.md` with their documentation links
- [ ] Quality gate wired with the architecture's real tools, settings and thresholds
- [ ] Gate commands identical locally and in CI
- [ ] CI has its own database, migrations, seed and test-value environment; no real secret in it
- [ ] Lockfile committed, not ignored
- [ ] Git hooks from the architecture installed by the setup command, versioned, and their bypass documented - or the architecture decided against them
- [ ] Services containerised with volumes and a health check
- [ ] One real migration, one test per level, all asserting something
- [ ] Browser E2E runner drives the walking skeleton locally and in CI with isolated state
- [ ] Browser projects match the app-shell support matrix and use user-facing locators without fixed sleeps
- [ ] A first-run browser failure remains visible; retry cannot turn a flaky test silently green
- [ ] Browser failure artefacts are retained as decided, successful-run noise is not
- [ ] Walking skeleton starts and reaches the database
- [ ] Seed command creates two tenants and one user per role, credentials documented
- [ ] `.env.local.example` complete; `.env.local` untouched; values printed for the user
- [ ] Committed in steps as each one ran, not once at the end
- [ ] Every documented command run from clean, restart and reset included
- [ ] Gate proven to go red when a test is broken; coverage floor proven to be enforced
- [ ] Documents corrected where reality differed
- [ ] `PROJ-1` claimed before the work, built on its own branch and worktree
- [ ] Proof written to `features/PROJ-1-scaffold/proof.md`, not only reported in the message
- [ ] `PROJ-1` set to `In Review`; `Done` left to `/merge`
- [ ] No application code beyond the walking skeleton
