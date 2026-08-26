# Kaitersberg

Skills that take a SaaS product from a briefing to merged features. This repository
contains the skills themselves - no product code. See [README.md](README.md) for the
pipeline.

## Layout
```
.claude/skills/<name>/SKILL.md    the skill: role, hard rules, phases, checklist
.claude/skills/<name>/template.md the document skeleton it fills
.claude/skills/build-loop/scripts/ the unattended runner shipped with that skill
.agents/skills/<name>/            the generated Codex port - never edited by hand
.agents/plugins/marketplace.json  the repo-local Codex marketplace
.github/                          CI, issue forms and the pull request template
plugins/claude/kaitersberg/ the self-contained Claude Code plugin
  skills/                           generated Claude skill bundle
plugins/codex/kaitersberg/  the self-contained Codex plugin
  skills/                           generated Codex skill bundle
.claude-plugin/marketplace.json   the repo-local Claude Code marketplace
scripts/update-installed-plugins.sh refreshes both local plugin installations
scripts/check.sh                  every check this repository makes, one command
scripts/lint-skills.py            the rules above, enforced instead of remembered
ruff.toml                         the explicit Python lint contract
.githooks/                        pre-commit and commit-msg, enabled with core.hooksPath
scripts/loop-feature.sh          compatibility entry point for the bundled runner
scripts/loop-status.sh           read-only status view over the persisted loop state
scripts/notify-ntfy.sh           example LOOP_NOTIFY notifier; optional, never a default
scripts/review-git.py            compatibility entry point for the bundled helper
scripts/buzz-doctor.py           diagnoses the local loop-to-Buzz path; read-only
                                 except for its explicit webhook probe
AGENTS.md                         hand-written, not generated: Codex's context file
                                  for this repository
```
`AGENTS.md` is the counterpart of this file for a Codex session, and it is the one
`AGENTS.md` in the tree that the port script does not produce. `.agents/skills/`
and both skill trees inside the plugin are build artefacts. The marketplace and
plugin manifests are maintained files.

## How a skill in here is written
- **English only.** The skills are English; the documents they produce follow the
  language of the user's briefing. That rule is stated inside each skill.
- **Structure:** frontmatter (`name` matching the folder, `description`,
  `argument-hint`, `user-invocable`, `allowed-tools`, `model`, plus
  `disable-model-invocation` on a skill only a person may start) · Role · Hard rules ·
  Abort conditions · numbered Phases · Checklist.
- **Skeletons live in a separate template file**, referenced from the skill as a
  relative link. Keeps the skill readable and the skeleton copyable.
- **Every rule carries its reason.** A rule without one is followed until somebody
  finds it inconvenient.
- **Say what must not happen**, not only what should. The abort conditions and the
  "never" rules are what stop a skill from improvising past a problem.
- **Sections are earned.** A skill that produces a document says which sections are
  always filled and which are deleted with a one-line reason. Empty headings read as
  "nobody looked".

## Invariants across the pipeline
- **Lifecycle rungs move forward once**, on `features/INDEX.md`: `Roadmap` → `Spec`
  → `Designed` → `Ready` → `In Progress` → `In Review` → `Done`, plus `Dropped`.
  `In Review` means the owned delivery loop - review, QA, corrections and CI - so
  findings do not bounce the board and force a default-branch merge for every
  correction. `/pr` moves nothing; `/merge` owns `Done` and cleanup.
- **The board is written on the default branch.** `features/INDEX.md` carries the
  claim, so a status committed inside a feature worktree is invisible until the
  work merges - and a second run picks up a feature that is already taken. Every
  skill that moves a rung while a worktree exists says this, and no feature branch
  touches the file.
- **Everything about a feature lives in `features/PROJ-x-<name>/`** - spec, design,
  tasks, review, test report, pull request body, evidence.
- **Where the documents are silent, ask.** Every skill that produces work carries
  this; it is the single rule that keeps an agent from inventing behaviour.
- **One test decides whether a document gets touched:** *would somebody who reads
  only the documents now believe something false?* Every skill that corrects a
  document uses that wording, and every one of them says that *checked, nothing to
  change* is a valid answer - otherwise documentation grows on every commit and
  stops being read.
- **Only `/scaffold` writes configuration or starts services.** Everything else
  plans or builds features.
- **`/review` and `/qa` fix nothing. `/audit` fixes nothing.** They report; `/build`
  repairs.
- **`/status` changes nothing at all.** It moves no rung and writes one generated
  page from what the other skills wrote. It is the one skill exempt from the rung
  rule above, and it says so in its own hard rules.
- **`.env.local` is never written by any skill.**

## Portability
The Codex port exists and is generated (below). Keep harness-specific mechanics
**named and few**: the
skill location, the frontmatter, the invocation, the context file, sub-agent
dispatch, the browser tools, the fresh-session requirement. Everything else - the
phases, the rules and their reasons, the skeletons, the checklists - stays
harness-neutral prose, and that is what makes a port cheap.

`.agents/skills/` is the Codex port, and it is **generated**: every file there is
written by `scripts/port-to-codex.py` from `.claude/skills/`, which is the single
source of truth. The same command produces the self-contained marketplace bundle
under `plugins/claude/kaitersberg/skills/` and
`plugins/codex/kaitersberg/skills/`. Never edit any of those three
generated trees -
edit the source skill and run:

```
python3 scripts/port-to-codex.py            # write the port
python3 scripts/port-to-codex.py --check    # fail if it is stale
```

The script does exactly the mechanics named above and nothing else: it copies
machine-readable `.json` templates and bundled `.py`/`.sh` runtime files
byte-for-byte with their executable modes, drops the frontmatter keys Codex has no
use for, rewrites `/skill` to `$skill`, `CLAUDE.md` to `AGENTS.md`, the bundled
runner locator, and the two Claude-specific tool names. If a skill ever needs
something the map does not cover, the script stops and says so - that is a harness
difference nobody has named yet, and it gets named in the map, not patched into the
generated file.

The plugin name is `kaitersberg`, so installed skills are deliberately
namespaced as `kaitersberg:<skill-name>` in both hosts. Bump the version in
both plugin manifests for a released plugin change and validate both manifests
before committing. During local plugin development,
`scripts/update-installed-plugins.sh` gives both manifests one shared cachebuster,
reinstalls both hosts and verifies their installed versions.

## Changing this repository
Never develop or push directly on the default branch, including as a maintainer or
administrator. Give every change its own branch and worktree, open a pull request,
and integrate it into `main` with GitHub's **Squash and merge**. This keeps review
and CI as the mandatory integration boundary and makes GitHub create and sign the
single commit on `main`, so the public history shows it as **Verified**.

## Changing a skill
Regenerate the Codex port and plugin bundle (`python3 scripts/port-to-codex.py`) and
commit all generated sides together - a stale port is worse than none.

Then run `scripts/check.sh`, which is also the pre-commit hook. It checks what a
person forgets: that the port is in step, that every handoff names a skill that
exists, that every referenced template is there, that the frontmatter is complete
and that the skill is still English. A handoff pointing at a skill that does not
exist is the failure mode this framework produces most easily, so it is the one
check that must never be skipped.

The invariants it cannot check are still yours to check: the status ladder, the
file paths, and whether the phases still say something true.
