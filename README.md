# Kaitersberg

Skills that take a SaaS product from a rough briefing to merged features, with an
agent doing the work and a human deciding the things worth deciding.

*The Kaitersberg is a ridge in the Bavarian Forest. Its tools live under
[grenzkamm](https://github.com/grenzkamm) - the crest the mountain stands on - and
what follows is named after the peaks around it.*

The premise: an agent that starts coding from a one-paragraph briefing builds
something plausible and wrong. So the first thing produced is not code - it is a
plan you can argue with. Everything after that reads the plan instead of guessing,
and where the plan is silent, the agent asks instead of inventing.

## Project status

Kaitersberg is in its public testing phase. The pipeline and document contracts may
still change before a stable 1.0 release, and it should not yet be treated as
production-proven automation.

The Claude Code path has been walked end to end to build demo SaaS products. Those
runs shaped the current checks and invariants, but they are not a claim that every
stack or production environment has been validated. The generated Codex port is
kept structurally in step and checked on every change; its complete product journey
has not yet been tested end to end. Codex users should expect rough edges and are
especially invited to report what does not carry across cleanly.

Forking, adapting and experimenting with Kaitersberg is explicitly welcome under
the MIT licence. Improvements are wanted: open an issue for a broad change or send
a focused pull request when the change is ready. A fork does not owe the upstream
project compatibility, but generally useful fixes and new evidence are very welcome
back here.

---

## Every step, in order

Once per machine, then once per product, then once per feature. Nothing here is
optional except the last block, and nothing is a suggestion: each step reads what
the previous one wrote.

| | Step | What it is |
|---|---|---|
| **0** | `/plugin marketplace add` · `/plugin install` | The skills, once per machine |
| **1** | `/plan-product <briefing>` | PRD, feature board with waves, data model, journeys, roles, app shell, `CLAUDE.md` |
| **2** | `/architecture` | The house style, decided once for all features |
| **3** | `/scaffold` | `PROJ-1`: a repository that actually runs, proven from a clean state |
| **4** | `/write-spec PROJ-x` | Stories, Given/When/Then criteria, edge cases, personal data, test plan |
| **5** | `/tech-design PROJ-x` | **The document you approve.** Every field, every role difference, no code |
| **6** | `/tasks PROJ-x` | Half-day tasks in parallel-safe batches, each traceable to a criterion |
| **7** | `/build PROJ-x` | The code, in its own worktree, test-first, batch by batch |
| **8** | `/review PROJ-x` | The diff against spec and design, **from a fresh session** |
| **9** | `/qa PROJ-x` | The running system, per criterion, in a browser, plus an adversarial pass |
| **10** | `/pr PROJ-x` | The pull request, assembled from the artefacts, confirmed before pushing |
| **11** | `/merge PROJ-x` | The merge, then `Done`, the worktree, both branches and the board |
| | **↻** | Steps 4 to 11 again, for the next feature in wave order |

[docs/process.md](docs/process.md) tells the same story the other way round: what
each stage decides, what it receives and hands over, where the work comes back and
where a person is required - the process rather than the commands.

Steps 7 to 10 run unattended: `scripts/loop-feature.sh PROJ-x`, one process per
stage, ending at the pull request and stopping wherever a person is required. See
[Running a feature unattended](#running-a-feature-unattended).

Findings from step 8 or 9 send work back to step 7, which then works the current
findings instead of the task list; step 8 runs again in a new session. Review and QA
reuse evidence by commit and run a targeted delta pass when the changed surface is
bounded; migrations, permission boundaries and broad shared changes force a full pass.

**When something happens that the order above does not cover:**

| Step | When |
|---|---|
| `/fix <bug>` | A defect found after a feature merged. Reproduce, root cause, failing regression test, fix, pull request - then `/merge BUG-n` |
| `/add-feature <what>` | A request arrives mid-flight. It says whether it is a feature at all, where it belongs, and which features it pushes back |
| `/audit` | After a whole wave, not after a feature: the drift no single review can see |
| `/status` | Somebody outside the terminal needs the state, as one page |

---

## What it needs

| | For | Why |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) 2.1.205+ or the Codex desktop app | everything | The skills are plugins for one of the two. The version floor is what the unattended loop needs (`--json-schema`) |
| `git` | everything | Features are built in worktrees |
| `python3`, `jq` | the loop and the dashboard | Both are standard-library only; `jq` reads the loop's event stream |
| `tmux` or `coreutils` | the loop, optionally | To detach it, and for a wall clock per stage. It runs without either |
| `shellcheck`, `ruff` | contributing | `scripts/check.sh` falls back to a syntax check when they are missing; `ruff.toml` owns the explicit Python rule set so a Ruff release cannot silently change the gate |

**No MCP server, no API key, no account beyond the harness you already use, and no
network at run time.** The skills read the repository they are in. A documentation
server or web search speeds up a library lookup and nothing more.

What the skills write in your repository - the specifications, designs, task lists,
reviews, reports and code - is yours. The licence covers the skills themselves.

## Optional integrations

Kaitersberg's default stays local and works without either integration. These are
places the pipeline can publish to or run alongside, not sources of truth and not
runtime dependencies.

| Project | Status | Role |
|---|---|---|
| [Buzz](https://github.com/block/buzz) ([website](https://buzz.xyz)) | Documented, optional | An Apache-2.0 workspace for product channels, planner and builder agents, workflow notifications and the status canvas. See [Kaitersberg over Buzz](docs/buzz.md) |
| [TaskView](https://github.com/Gimanh/taskview-community) | Candidate, not implemented | A future one-way publisher for the feature board. TaskView is source-available rather than OSI-approved open source; Kaitersberg would never read a dragged status back into `features/INDEX.md` |

Kaitersberg is an independent project and is not affiliated with or endorsed by
Block, Buzz or TaskView. Product names and trademarks belong to their respective
owners.

![The board and the loops running against it](docs/dashboard-board.jpg)

![One feature: what is still open, what the round before settled, what landed since, and every task by batch](docs/dashboard-feature.jpg)

<sub>`scripts/loop-dashboard.py`, photographed against `examples/demo-product` -
invented data, not anybody's project.</sub>

---

## How you work with it

### Once, at the start of a product

| | You run | You get | You decide |
|---|---|---|---|
| 1 | `/plan-product <briefing>` | PRD, feature board, data model, journeys, roles, app shell, local dev plan, `CLAUDE.md` | The feature cut and the build order - one checkpoint, before the rest is written |
| 2 | `/architecture` | `docs/architecture.md`: the house style, decided once | Two to four load-bearing decisions, each with its alternative and both costs |
| 3 | `/scaffold` | `PROJ-1`: a repository that runs - services in containers, migrations, seed data, test harness, quality gate, CI | Nothing, unless a port or a tool choice was left open |

After step 3 the documented commands have actually been run, so `docs/local-dev.md`
is true rather than merely written.

### Install the framework as a plugin

The repository is a marketplace for both Codex and Claude Code. The installed
plugin is named `kaitersberg`; its namespace prevents collisions with
unrelated skills that happen to use names such as `architecture` or `review`.

Both hosts can add this repository as a marketplace from its URL or from a local
clone. The URL form needs nothing checked out:

```bash
codex plugin marketplace add https://github.com/grenzkamm/kaitersberg
codex plugin marketplace add /absolute/path/to/kaitersberg   # or a clone
```

Restart the ChatGPT desktop app, open the Plugins Directory, select the
**Kaitersberg** source and install the plugin. Invoke a skill as, for
example, `$kaitersberg:architecture`.

For Claude Code, run these commands inside a session:

```text
/plugin marketplace add https://github.com/grenzkamm/kaitersberg
/plugin install kaitersberg@kaitersberg
```

A local clone works in place of the URL, which is what you want while changing
skills: `/plugin marketplace add /absolute/path/to/kaitersberg`.

If Claude Code asks for a reload, run `/reload-plugins`. Invoke the same workflow
as `/kaitersberg:architecture`. Both marketplaces can also be added from
the Git repository instead of a local checkout; each host then manages updates
through its marketplace command.

After changing skills and regenerating the bundles, refresh both local plugin
installations from the framework checkout with:

```bash
scripts/update-installed-plugins.sh
```

The script validates the generated port and both marketplace manifests, adds one
shared `+codex.local-<UTC timestamp>` cachebuster to the two plugin versions,
updates Codex and Claude Code, and verifies the installed versions. The cachebuster
changes are intentional for local iteration, but are not a semantic release
version. For a release, set the intended version in both manifests, commit it, and
run the script with `--no-version-bump`. Use `--dry-run` to inspect the operation
without changing files or installations. Start a new Codex thread and restart
Claude Code after the update so active sessions do not retain the old skill
instructions. Product repositories require no update command of their own.

Installing the plugin supplies the workflows, not a product's planning artefacts.
Create or copy the product's `CLAUDE.md`/`AGENTS.md`, `docs/` and
`features/INDEX.md` into its own repository before invoking architecture there.
With the installed plugin, use the namespaced forms
`$kaitersberg:architecture` or
`/kaitersberg:architecture`.

### Then, once per feature, in the wave order the board gives you

| | You run | You get | You decide |
|---|---|---|---|
| 4 | `/write-spec PROJ-x` | `spec.md`: stories, Given/When/Then criteria, edge cases, personal data, security, test plan | Only scope changes, product decisions or a cut above the review budget; otherwise a handoff summary |
| 5 | `/tech-design PROJ-x` | `design.md`: every field, the admin/user difference, the flow - readable without code | **You approve this.** It is the sign-off document |
| 6 | `/tasks PROJ-x` | `tasks.md`: half-day tasks in batches, each traceable to a criterion | Only behaviour/design gaps or a cut above the review budget; otherwise a handoff summary |
| 7 | `/build PROJ-x` | The code, in its own worktree, test-first, batch by batch | Only what the plan left silent |
| 8 | `/review PROJ-x` | `review.md`: findings against spec and design - **run this in a fresh session** | Whether findings are worth fixing |
| 9 | `/qa PROJ-x` | `qa.md`: a verdict per criterion, a browser walkthrough, an adversarial pass | Nothing - it tells you if it is production ready |
| 10 | `/pr PROJ-x` | The pull request, assembled from all of the above | Whether to push |
| 11 | `/merge PROJ-x` | The merge, then the cleanup: worktree, branches, board | Whether to merge - this is the irreversible one |

`/merge` is what sets the feature to `Done`, clears the owner, removes the worktree
and both branches, and says which features just became pickable. A person starts it;
no model does.

### Running a feature unattended

`/build`, `/review` and `/qa` are separate sessions on purpose: a reviewer who
watched the feature being built shares the assumptions that produced its bugs. One
script does that separation for you, one process per stage, and ends by opening the
pull request - in the product repository:

```bash
cd <product repo> && git checkout main
ROUNDS=3 <framework>/scripts/loop-feature.sh PROJ-x     # build → review → qa → pull request
PR=0     <framework>/scripts/loop-feature.sh PROJ-x     # ... stopping before the pull request
```

The unattended review gets no general shell and no raw `git *` permission. It uses
`scripts/review-git.py`, whose fixed queries can inspect status, diffs, commits,
worktrees and tracked content without admitting mutating Git commands, aliases,
external diff drivers or inherited repository state. The same restriction is
inherited by its parallel review lanes.

Build gates also keep their raw output out of the agent context and the feature
worktree: every command gets a unique temporary log. Only bounded final or failing
extracts are committed under the feature's `evidence/gates/` directory. Schema-v2
`verification.json` records the code `tested_sha`; the only permitted descendant is
the commit containing that manifest and its evidence. QA can therefore reuse a
green gate without treating a later product change as already tested.

The first run creates a state file and an atomic lock below Git's common directory.
A later invocation resumes that state. `START_STAGE=review` imports an already
existing manual feature only when no state exists; `LOOP_RESET=1` archives the old
state and starts again. `INFRA_RETRIES` controls bounded retries for a stage that
returns no structured outcome. A restart cannot silently reset an exhausted
`ROUNDS` budget; inspect the reports, raise the budget deliberately or archive the
state with `LOOP_RESET=1`. Only one loop for a feature may hold the lock.

A run takes hours, and every stage is a child of the shell that started it - close
that terminal, or end the agent session that started it for you, and the stage in
flight dies with its work uncommitted in the worktree. Detach it if it has to
outlive the window:

```bash
tmux new -d -s PROJ-x 'ROUNDS=3 <framework>/scripts/loop-feature.sh PROJ-x'
tmux attach -t PROJ-x     # look; ctrl-b d to let go again
```

`tmux new -d` runs the command directly. A wrapper that types it into an
interactive login shell instead is a worse start for an unattended run: anything
that asks a question at startup - an update prompt, a version manager - holds the
command until somebody answers, and the run looks started when it is not.

Whatever holds the run, keep it out of the feature worktree: that is where
`/build` writes, and a second agent sitting in it is the collision worktrees exist
to prevent. The loop belongs in the product repository on the default branch,
which is also where the board is written.

The dashboard finds the run whichever way it was started - it reads the process
list, not the terminal.

Findings send the round back to `/build`; the next round reviews the delta in a new
session and QA retests the affected criteria. The runner persists its stage, SHA and
per-stage budgets below Git's common directory, so restarting it resumes Review, QA
or PR instead of paying for a no-op Build. It stops in exactly three places: when the plan is silent and a decision
is needed (exit 2), when one stage comes back without a green result `ROUNDS` times (exit 1), and
before `/merge` always. Transient harness failures are retried three times without
spending a product round. A green run then opens the pull request, because starting
the loop is the confirmation `/pr` asks for, given in advance for one feature and
one branch; `PR=0` stops before that step instead, and `/merge` is never automated
at all. Every invocation ends with what it cost: stages, turns, wall clock, tokens;
the state file carries lifecycle attempts across invocations.

Watch it while it runs:

```bash
python3 <framework>/scripts/loop-dashboard.py     # http://localhost:8787
```

The board as columns, one per rung, with what each loop is doing right now, what
each feature's review and test report decided, its findings, its tasks by batch,
and what the agents have spent on it. It renders from the board, the loop log and
git on every request, so there is nothing to keep in sync - and it changes nothing.

The same server exposes that read model as a versioned JSON API for local tools and
optional one-way publishers:

```bash
curl http://localhost:8787/api/v1                 # discover the endpoints
curl http://localhost:8787/api/v1/snapshot        # the complete read model in one response
curl http://localhost:8787/api/v1/features        # board rows and their derived state
curl http://localhost:8787/api/v1/features/PROJ-3 # one feature including tasks and findings
curl http://localhost:8787/api/v1/loops
curl http://localhost:8787/api/v1/bugs
```

Every response declares `schema_version: 1` and `read_only: true`. Only `GET` and
`HEAD` are accepted; `POST`, `PUT`, `PATCH` and `DELETE` return `405`. The API has
no database and no status-changing endpoint: `features/INDEX.md`, the loop state,
reports, processes and git remain its inputs, never its outputs. The server still
binds to `127.0.0.1` only. Putting it behind a network listener would require an
explicit authentication and data-exposure design first, because findings and
branch names can contain product information.

Tell the sessions in the product repository that this exists: `/plan-product`
writes an *Unattended runs* section into that repository's `CLAUDE.md` for exactly
that, because a session three weeks later starts there knowing nothing.

For a product connected to Buzz, diagnose the whole local delivery path from the
product repository instead of inspecting its state files and tmux processes by
hand:

```bash
python3 <framework>/scripts/buzz-doctor.py PROJ-3
python3 <framework>/scripts/buzz-doctor.py PROJ-3 --follow
```

The read-only default checks the board, loop state, process, lock, log activity and
last notification receipt. Public Buzz channel and workflow identifiers add relay,
membership, workflow-run and canvas checks; `--probe-webhook` is the one explicitly
active mode and sends one visible workflow trigger. The complete setup and command
line are in [docs/buzz.md](docs/buzz.md#debugging-from-the-terminal).

### When something goes wrong

- `scripts/buzz-doctor.py PROJ-x` distinguishes a stopped or stalled loop, a stale
  lock and a failed Buzz notification, then gives the next concrete action. Use
  `--json` for a support artifact that contains no webhook secret.
- `/review` or `/qa` leaves the owned feature on `In Review` and writes the current
  findings. `/build` works that list instead of the tasks, then it goes round again
  - delta `/review` in a fresh session, then targeted or full `/qa` according to the
  blast radius.
- `/fix <bug>` is the short path for a bug: reproduce, root cause, failing
  regression test, fix, pull request. No seven documents. If the fix turns out to
  change behaviour, it stops and routes you to `/write-spec`.
- `/audit` reads the whole repository against the architecture and the plan. Run it
  after a wave, not after a feature - it finds the drift no single review can see.

### When something new arrives mid-flight

`/add-feature <what is missing>` puts a request that came after planning onto the
board. It first decides whether it is a feature at all - or a change to an existing
one, a bug, or scope creep for the non-goals list. Then it places it by dependency,
rechecks the parallel safety of the wave it joins, **says by name which features it
pushes back**, and tells you whether anything currently being built should pause
because its design just went stale. Nothing is ever renumbered.

---

## The two rules that make it work

**Where the documents are silent, the agent asks.** An invented behaviour is a
defect that passes review, because nobody specified otherwise. Every skill carries
this rule, and it is why the specification is worth its length.

**Lifecycle rungs only move forward.** `Roadmap` → `Spec` → `Designed` → `Ready` →
`In Progress` → `In Review` → `Done`, plus `Dropped` for a feature that gets cut.
Review, QA, corrections and CI all stay `In Review`; their finer state lives in
the feature artifacts and the persisted loop state. The board still says who owns
the work without oscillating on every finding.

---

## What the planning produces

```
CLAUDE.md              What every later session reads first
docs/PRD.md            Vision, users, features, success criteria, constraints
                       incl. the non-functional ones, non-goals, risks, and
                       every deliberate deviation from your briefing
docs/data-model.md     Entities, relations, tenant isolation, the vocabulary -
                       and what is deliberately not an entity
docs/journeys.md       Signup to first value in n steps, the empty account,
                       one core journey per role
docs/access.md         Roles, the full permission matrix, plan gating
docs/app-shell.md      Shells per auth state, layout, navigation, route map
docs/design-system.md  Only when you supplied a mockup. Never invented.
docs/sources/          Only when material came from outside - regulations,
                       standards, contracts, mockups - with what rests on each
docs/local-dev.md      Ports, commands, external accounts, deploy target
docs/architecture.md   The house style, incl. the quality gate with its numbers
features/INDEX.md      Every feature: priority, dependencies, size, wave, scope
.env.local.example     Every variable, placeholders for secrets
```

`/plan-product` and `/architecture` write no code and no configuration. `/scaffold`
is the only skill allowed to write configuration and start services. No skill ever
writes `.env.local`.

---

## Conventions

- **Feature IDs** are `PROJ-1 … PROJ-n`. `PROJ-1` is always the scaffold.
- **Priority follows dependencies**, not enthusiasm. P0 is what other features
  cannot exist without.
- **Build order is waves.** Wave 1 depends on nothing; wave *n* only on earlier
  waves. Within a wave, features are cut so they can be built in parallel.
- **Wave 1 is demoable.** Dependency order alone gives you three weeks of auth and
  empty tables, so the thinnest end-to-end slice is pulled forward.
- **Specs are written just in time** - one board row per feature, the full document
  only when the feature is next. Fourteen specs written up front rot unread.
- **Everything about a feature lives in its folder**, including the evidence.
- **Tests come before the code**, and each is seen failing before it is made to
  pass. A test that was never red proves nothing.
- **Commits** are `feat(PROJ-x): …`, `fix(BUG-n): …`, `docs(PROJ-x): …`.

---

## Repository layout of a product built this way

```
CLAUDE.md
docs/                            The plan and the architecture
docs/audits/YYYY-MM-DD.md        Drift reports from /audit
docs/sources/                    What came from outside, and what rests on it
docs/status.html                 The stakeholder page, generated by /status
features/INDEX.md                The board
features/PROJ-x-<name>/          One folder per feature
  spec.md · design.md · tasks.md · verification.json
  review.md · qa.md · delivery.md · pr.md
  evidence/                      Bounded build-gate evidence plus QA screenshots,
                                 recordings and captured responses
bugs/INDEX.md · bugs/BUG-n-*.md  The short path
.worktrees/PROJ-x-<name>/        One worktree per feature being built - unless a
                                 workspace environment owns worktrees, which then
                                 keeps them in its own place
```

## All fifteen skills

**Once per product**
| Skill | Does |
|---|---|
| `/plan-product` | Briefing → PRD, feature board with waves, data model, journeys, roles, app shell, local dev, `CLAUDE.md` |
| `/architecture` | The house style: modules, request path, isolation, rules, errors, logging, migrations, tests, quality gate |
| `/scaffold` | `PROJ-1`: the repository that runs - services, migrations, seed, harness, gate, CI - proven from a clean state |

**Once per feature**
| Skill | Does |
|---|---|
| `/write-spec PROJ-x` | Stories, Given/When/Then criteria, edge cases, personal data, security, test plan |
| `/tech-design PROJ-x` | The approval document: every field, the admin/user difference, the flow, without code |
| `/tasks PROJ-x` | Half-day tasks in parallel-safe batches, every one traceable to a criterion |
| `/build PROJ-x` | The code, own worktree, test-first, batch by batch - also the mode that works findings |
| `/review PROJ-x` | The diff against spec and design, from a fresh session |
| `/qa PROJ-x` | The running system per criterion, in the browser, plus an adversarial pass |
| `/pr PROJ-x` | The pull request, assembled from the artifacts |
| `/merge PROJ-x` | The merge, and the worktree, branches and board it clears |

**When needed**
| Skill | Does |
|---|---|
| `/add-feature <what>` | Places a request that arrived after planning, with its true cost to the waves |
| `/fix <bug>` | Reproduce, root cause, failing regression test, fix, pull request |
| `/audit` | The whole repository against the architecture and the plan - the drift no review sees |
| `/status` | The board as one page a stakeholder reads: done, running, waiting for a decision, stalled |

---

## Harnesses

The framework is authored for **Claude Code** and generates its **Codex** port from
the same source. Both variants are distributed through one namespaced plugin.

Everything that carries the actual thinking - the phases, the hard rules, the
document skeletons, the status ladder, the checklists - is harness-neutral prose and
ports unchanged. What is Claude Code specific is small, and listed here so a port
knows exactly what it has to replace:

| Claude Code specific | What it is | What a port needs |
|---|---|---|
| `.claude/skills/<name>/SKILL.md` | Where a skill lives and is discovered | The equivalent location for that harness |
| Frontmatter `user-invocable`, `allowed-tools`, `model`, `argument-hint`, `disable-model-invocation` | How the harness registers and constrains a skill - the last one keeps `/scaffold` from being called by a model that thought some configuration would help | The equivalent fields, or nothing |
| `/skill-name` invocation | How a user starts one | The harness's own invocation |
| `CLAUDE.md` | The file every Claude session reads first | The harness's context file - `AGENTS.md` for Codex. Generated templates use an explicit plain-path reading list, because Claude's `@path` imports are silent no-ops in Codex |
| Sub-agent dispatch in `/build` | One agent per task within a batch | Any way to run tasks concurrently, bound to their declared write sets |
| `claude-in-chrome` tools in `/qa` | The browser walkthrough | Codex Browser with Computer Use (`@Browser`); Developer mode/full CDP for console, network, DOM and styles |
| Fresh-session requirement in `/review` | An agent with no memory of the build | Whatever produces a reviewer that did not build it |
| Worktree tooling in `/build` | Isolation per feature | Plain `git worktree` works everywhere |

Independent of the harness, the skills detect one **workspace environment**, because
it owns things they would otherwise create behind its back:

| Environment | Detected by | What the skills use instead |
|---|---|---|
| [Orca](https://www.onorca.dev) | `ORCA_WORKTREE_ID` set and `orca` on the `PATH` | the `orca-cli` skill for worktrees in `/build`, `/fix`, `/scaffold` and `/pr`, and Orca's own browser for the `/qa` walkthrough |

Nothing else changes: the phases, the rules and the reports are the same. Whatever
creates a worktree also removes it - mixing the two mechanisms leaves half a
workspace behind.

The rest - the discipline that a test must be seen failing, that a batch needs
disjoint write sets, that a design is approved before tasks are cut, that where the
documents are silent the agent asks - is not harness-specific at all.

### Tools it assumes, and tools it does not

**No MCP server is required.** Nothing in the fifteen skills fails because a
server is missing, and that is deliberate: a rule that only works with one vendor's
tool installed does not survive the port, and does not survive the day that tool is
down.

| Tool | Needed by | Required? |
|---|---|---|
| Project-owned browser E2E runner | `/build`, `/review`, `/qa` and CI for products with a web UI | Yes for observable UI criteria. The architecture chooses the runner and exact local/CI commands; the default for a new web project may be Playwright. These tests live in the repository and remain runnable without an agent browser |
| Browser automation | `/qa`'s walkthrough, `/fix`'s browser loop | For those phases, yes - `claude-in-chrome` on Claude Code; the Browser plugin with Computer Use in the Codex desktop app. Codex CLI and the IDE extension do not provide the built-in browser. Without browser automation, affected criteria are `blocked`; the report must not claim that the walkthrough passed |
| A documentation server (Context7 or similar), or web search | `/build` and `/fix`, when a library API is uncertain | No. It only speeds up the lookup. The rule points at the lockfile, the installed types and `docs/local-dev.md`'s **Stack & versions** table first, because those are the only sources guaranteed to match the version that will actually run |
| `git worktree` | `/build`, `/fix` | Yes, and it is everywhere |

Install a documentation server at **user level**, not into the product repository.
Committing one into a project makes it a dependency of that project's pipeline,
which is exactly what the first paragraph avoids.

For Codex browser QA, install and enable the **Browser** plugin in the ChatGPT
desktop app and invoke it as `@Browser`. Enable Browser Developer mode with full
CDP access when the walkthrough must inspect console output, network traffic, the
DOM or applied styles. The skill checks availability before the walkthrough and
marks browser-dependent criteria `blocked` when the capability is unavailable.

The two browser layers have different jobs. The project-owned E2E suite is the
repeatable gate: isolated fixtures, user-facing locators, observable waits, the
product's supported browser/viewport projects, and traces or screenshots on
failure. It runs locally and in CI. The agentic walkthrough then checks the running
product for visual states, wording, keyboard and focus behaviour, console output,
failed requests and adversarial journeys. A retry-only pass is reported as flaky;
the walkthrough cannot turn a missing or failing automated suite green.

`.agents/skills/` is the Codex port of all fifteen skills, and it is **generated**
rather than maintained: `scripts/port-to-codex.py` writes it from `.claude/skills/`,
applying exactly the replacements in the table above. The same run refreshes the
self-contained skill trees in `plugins/claude/kaitersberg/` and
`plugins/codex/kaitersberg/`, so marketplace installs never mix
harness-specific frontmatter. A change is made once, in `.claude/skills/`, and all
bundles are regenerated:

```
python3 scripts/port-to-codex.py            # write the port
python3 scripts/port-to-codex.py --check    # fail if it is stale
```

Never edit `.agents/skills/` or either generated plugin skill tree. Two rows of the
table are not automatable and stay open on the Codex side: sub-agent dispatch in `$build`
(the port keeps the prose; the harness has to supply the concurrency) and the
fresh-session requirement in `$review`.

The port is regenerated and checked on every commit - `scripts/check.sh` fails when
it is stale. Its structure and generated content are covered; the full Codex product
journey remains deliberately marked untested until somebody walks it end to end.

## Where the documents live, and what is planned around that

The specification, the design, the task list, the review and the test report are
**files in the repository**, and they stay there. The reason is one test: does this
artifact have to be true *at a commit*? A spec does - it must sit in the same diff
as the code that implements it, and it must still be findable at that commit a year
later, which is the only way `/audit` can compare `data-model.md` field by field
against the real schema, and the only way an agent can read it in a worktree with no
network and no credentials.

Status, ownership, discussion, notification and approval are the opposite: they are
about *now*, never about a commit. That is what an issue tracker is genuinely better
at, and that is the only part worth moving out.

So the direction of travel is fixed, and stated here rather than discovered by every
user separately: **the documents stay in the repository, the tracker may hold state.
Never the other way round.** Two places that both claim to hold the specification is
the failure `/audit` spends its time finding.

### Planned: making the tracker optional, in three steps

None of this is built yet. It is written down so the shape is decided before the
first person asks, and so nobody solves it by making the core configurable.

**The rule it has to obey**: optional means the default works without it. Nothing
below may add a question to a fresh clone, and none of it may turn
`features/INDEX.md` into a configurable thing - the moment the board is pluggable,
every one of the fifteen skills grows a branch at "move the rung", every
contributor has to hold both branches in their head, and the one invariant that
holds the pipeline together becomes a convention.

| Step | What it is | What it touches |
|---|---|---|
| **0 - files** | Today. `features/INDEX.md` is the board, offline, no configuration, nothing to set up | - |
| **1 - intake** | Bugs and requests arrive as issues: `/fix #123` and `/add-feature #124` read the issue instead of a description in chat, with its reporter, its date and its attachments - which are the artefacts `/fix` asks for anyway when no loop can be built | `/fix`, `/add-feature`. **No status, so no invariant** |
| **2 - publish** | One optional skill pushes the board **one way** into GitHub Projects, Linear, Jira, Plane or [TaskView](https://github.com/Gimanh/taskview-community): one ticket per feature, status mirrored, a link back to the feature folder. Nothing comes back, so there is no drift and no second truth | One new skill, no existing one |

The configuration for both sits in **one document in the repository**, written by a
setup skill that only a person starts (`disable-model-invocation`, as `/scaffold`
already does). It names the system and what the four operations are called on it:
read the board, move a rung, file a ticket, link back. **When that document is
absent, step 0 is what runs**, and nobody is asked anything.

TaskView is a candidate for the first self-hosted adapter: its custom Kanban
statuses, dependencies and API fit the feature board. It could replace the shared
presentation of that board, but not the local reader that derives live stages,
findings, attempts and cost from loop state, reports, processes and git. The
existing dashboard therefore remains the offline default and live fallback; a
TaskView integration only publishes a read-only projection and never accepts a
dragged card or another status change back into `features/INDEX.md`.

Worth knowing before reaching for step 2: the usual reason to want a tracker is that
somebody outside the terminal needs to see the state - and `/status` already answers
that with one page and no system at all.

### Also queued for the same treatment

The same three parts - a setup skill, one configuration document, skills that name
the role instead of the tool - are what the rest of the hard-coded conventions need
when somebody's project does not match them: the `PROJ-` prefix, the wave layout,
and the `.worktrees/` location. All three are smaller than the tracker, and none of
them is worth abstracting before a second project has asked.

## Considered next

None of this is built. It is written down so the reasoning survives, and so the
next person does not solve any of it by making the core configurable.

| | Idea | Why, and what it must not become |
|---|---|---|
| **1** | **`LOOP_NOTIFY`** - the loop runs one command of your choosing when it ends or stops | The loop reports an exit code and nothing else, which is its one named gap. A hook that takes any command works with Slack, ntfy, a desktop notifier or a post into a workspace; binding the script to one vendor solves the same problem in a way that only helps one person |
| **2** | **A check that a skill change demands a version bump** | `scripts/check.sh` verifies that both plugin manifests agree on a version. It does not notice that ten skill files changed while the version stood still, which is exactly what happened on the day the checks were written |
| **3** | **`loop-next`** - take the next feature the pick rule allows and build it, then the one after | The dashboard already computes *pickable*: status `Ready`, no owner, every dependency `Done`. Turning that into a queue changes the unit from one feature unattended to a whole wave unattended, and it inherits every place the loop already stops. It must inherit them, not add new ones |
| **4** | **A [Buzz Projects](https://buzz.xyz/projects) activity adapter** - give each feature branch a shared channel and publish loop stages, commits, review and QA outcomes, approval requests and links to the repository artefacts as signed events | Buzz is a self-hosted relay where people, agents, workflows and git events share one searchable history, so the delivery loop fits it better than a generic notification does. Its project binding, issues, approval and merge surfaces still have to become stable enough to target. Until then this remains step 2 of the plan above: **one way out.** `features/INDEX.md` stays authoritative, and neither a Buzz event nor an action in Buzz may move a rung or merge a branch back in Kaitersberg |

**Deliberately not planned.** Dragging a card between columns on the status page:
it would set a rung no skill wrote, which is the one thing the board must never
show. Reading feature state back out of a tracker, for the reason in row 4. A
setup skill whose whole job is a paragraph - `/plan-product` already writes the
file that paragraph belongs in. And a branch in the loop that detects Orca and
starts itself in its terminal: `/build` has one because Orca *owns* worktrees, and
a git worktree Orca does not know about is two systems disagreeing about state.
Nothing owns where the loop runs - a tmux session, an Orca tab and a plain
terminal are equally right, and none of them needs the loop to know which. A
branch that saves typing one command
is not the same kind of thing as a branch that keeps two systems from
contradicting each other, and treating them alike is how a harness axis becomes a
fork.

## Working on this repository

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before a broad
change and follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities
through the private route in [SECURITY.md](SECURITY.md), never through a public
issue.

The checks are one command. The pre-commit hook and GitHub Actions run that same
command, so there is no second opinion about what green means:

```bash
git config core.hooksPath .githooks   # once per clone
scripts/check.sh                      # what the hook runs
```

It verifies that the Codex port and both plugin bundles are in step with
`.claude/skills/`, that every skill still obeys the rules this repository states
about skills - frontmatter, a template link that resolves, a handoff that names a
skill which exists, English - that the shell and Python under `scripts/` lint and
parse, and that the plugin manifests are valid JSON agreeing on one version. The
hook additionally refuses a staged `+codex.local-` version: that cachebuster is for
a local install and was never a release.

`scripts/lint-skills.py --selftest` checks the linter itself against a deliberately
broken skill, because a rule that never fires is decoration.

## This repository

```
.claude/skills/<name>/SKILL.md    The skill: role, hard rules, phases, checklist
.claude/skills/<name>/template.md The document skeleton it fills
.claude/skills/<name>/*.json      Machine-readable templates, copied verbatim
.agents/skills/<name>/            The Codex port - generated, never edited by hand
.agents/plugins/marketplace.json  The Codex marketplace catalog
.claude-plugin/marketplace.json   The Claude Code marketplace catalog
.github/                          CI, issue forms and the pull request template
plugins/claude/kaitersberg/ The self-contained Claude Code plugin
plugins/codex/kaitersberg/  The self-contained Codex plugin
scripts/port-to-codex.py          What generates it, and the only place the
                                  harness differences are written down
scripts/update-installed-plugins.sh Refresh both cached local plugin installs
scripts/loop-feature.sh           Build, review, qa and the pull request unattended,
                                  one process per stage, stopping where a person
                                  is required
scripts/review-git.py             Fixed read-only Git queries for unattended review
scripts/loop-dashboard.py         The board and the running loops as a live page
scripts/buzz-doctor.py            Read-only terminal diagnosis from loop to Buzz,
                                  plus one explicit active webhook probe
ruff.toml                         The explicit Python lint contract
scripts/check.sh                  Every check this repository makes, one command
scripts/lint-skills.py            The rules in CLAUDE.md, enforced rather than recalled
.githooks/                        pre-commit and commit-msg, enabled per clone with
                                  git config core.hooksPath .githooks
CLAUDE.md                         How a skill here is written, and the invariants
AGENTS.md                         The same for a Codex session - hand-written, the one
                                  file the port does not generate
```

**Walked end to end on demo SaaS products, and not finished.** With Claude Code,
features have been planned, specified, designed, built, reviewed, tested and merged,
including a review that sent one back for a defect no test had caught. What those
runs corrected is in the git history of this repository, which is the honest measure
of how much a written-but-unrun skill is worth. The Codex path has not yet had the
same end-to-end run. Three skills have still never run: `/fix`, `/add-feature` and
`/audit`. Briefings and all generated product documents belong in dedicated product
repositories, not in this one.

Skills are written in English regardless of the briefing language; the documents
they produce follow the language of your briefing. See [CLAUDE.md](CLAUDE.md) for
how a skill in here is written and which invariants hold across all of them.

---

## Acknowledgements

Kaitersberg was inspired in part by workflow ideas from the
[AI Coding Starter Kit](https://github.com/alexpeclub/ai-coding-starter-kit) by
Alex Sprogis. Kaitersberg is an independent implementation and is not affiliated
with that project.

---

## Licence

MIT - see [LICENSE](LICENSE). Forking, modification and redistribution are welcome.
The documents and code the skills produce in your own repository are yours; the
licence covers the skills, scripts and templates here.
