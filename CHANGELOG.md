# Changelog

Versions are the plugin versions in both manifests. The format is kept short: what
changed, and why it was wrong before.

## Unreleased

**The unattended delivery loop is now a self-contained skill.**
`/kaitersberg:build-loop` and `$kaitersberg:build-loop` resolve the runner bundled
inside the installed plugin, so product repositories no longer need to know a
Kaitersberg checkout or plugin-cache path. The old top-level script paths remain
compatibility entry points for framework contributors. Detached starts now return
their tmux session and durable launcher output/exit paths without claiming delivery
completed, including when the runner fails before creating state or events. The
read-only status helper ships in the same runtime bundle and exposes that failure.

**Delivery feedback is cheaper and keeps its evidence.** Batch tasks now carry
targeted gates while the complete gate runs once at integration. Specifications
and designs surface form accessibility, write collisions, product-wide error
behaviour and permission-guard mutation checks before build. Review and QA keep
one bounded, SHA-marked current report and archive prior snapshots separately;
delivery stages read only the relevant board rows.

**Rejected Claude rate limits stop the loop immediately.** A
`rate_limit_event` with status `rejected` terminates the stage process group,
records the reset time, notifies the operator and exits without consuming a stage
attempt or sleeping through infrastructure retries.

**Loop observation is bounded and repository-specific.** A configured notifier
now has the promised wall-clock limit even on macOS without coreutils, including
its child processes. The status command identifies a running loop through the
PID recorded beside this repository's lock instead of matching any same-named
feature process on the machine. The status template now takes its scope line from
the board, as the skill already required.

**The privacy boundary is explicit.** Kaitersberg can surface personal data,
retention, access and security questions, but its recommendations are not legal
advice and do not make a product GDPR compliant. The README now names the
product-specific legal and operational work that remains before production use.

**The local loop dashboard and JSON API are removed.** Their progress view
duplicated what Claude or Codex can answer from the board, feature artifacts and
persisted loop state, while adding a server, API contract, fixture product,
screenshots and a separate test surface. `/status` remains the explicit way to
write a self-contained stakeholder page; `loop.log` and the state file remain the
machine-readable record of an unattended run.

## 0.5.0 - 2026-08-25

**First public test release.** Kaitersberg ships the complete specification-first
product and feature pipeline for Claude Code plus a generated, continuously checked
Codex port. The Claude Code path has built demo SaaS products end to end; the Codex
journey is available for testing and feedback but has not yet been exercised end to
end.

**The feature loop resumes instead of replaying finished work.** A typed state file
below Git's common directory records Build, Review, QA and PR outcomes, HEAD and
retry budgets; one atomic lock prevents duplicate loops. Review corrections, QA
failures, CI failures and conflicts now have explicit return paths, while missing
harness results use a separate bounded retry budget.

**Feedback rounds pay for the changed surface.** Build runs targeted batch gates
and one integrated full gate, Review uses parallel full lanes or a delta pass, and
QA reuses SHA-bound evidence for unchanged criteria while retesting the affected
paths. Machine-readable verification and delivery handoffs make that reuse
auditable.

**The board no longer oscillates during delivery.** Review, QA, corrections and CI
stay in the owned `In Review` lifecycle rung. Planning now treats 20 acceptance
criteria, 10 tasks or 5 sequential batches as split tripwires, and Spec/Tasks wait
for approval only when they introduce a decision or exceed that budget.

**The runner has behavior tests.** Transition and fake-CLI integration tests cover
green delivery, resumability, feedback, CI return, retry budgets and duplicate-run
locking; the repository gate runs them on every check.

**Headless review no longer treats all Git as read-only.** Its constrained session
uses a fixed query helper instead of `Bash(git *)`, which also admitted checkout,
clean, apply and shell aliases. Gate output now uses unique temporary raw logs and
committed bounded extracts tied to the tested code SHA, so one suite cannot erase
another's evidence or leave an unexplained dirty worktree.

**The board tells the truth while work is running.** The claim, `In Review` and both
push-backs were committed inside the feature worktree, so they reached the default
branch only when the work merged - by which point `/merge` was setting `Done`
anyway. On the default branch a feature went from `Ready` straight to `Done`, and
the pick rule reads exactly that field: a second `/build` saw `Ready`, no owner, and
would have claimed a feature somebody was already building. Every rung that moves
while a worktree exists is now written in the default branch's checkout, and no
feature branch touches `features/INDEX.md`. `/fix` carries the same change for
`bugs/INDEX.md`.

**`/review` can write the two files its own phases require.** Its `allowed-tools`
listed no `Write` and no `Edit`, while the skill is told to write `review.md` and to
set the row back to `In Progress`. The only route left was a shell heredoc.

**`/tech-design` names the keys before anybody approves.** A build stopped to ask
where the key for an audit pseudonym came from; the design had demanded a stable,
non-reversible actor reference and never said what it was derived from. The design
now earns a *Secrets and keys* section whenever a feature signs, hashes,
pseudonymises or encrypts anything.

**`/fix` points at the board skeleton** where it creates `bugs/INDEX.md`, and that
skeleton now names who sets each rung, the way the feature board does.

**New, outside the skills:** `scripts/loop-feature.sh` runs build, review and qa
unattended, one process per stage, stopping where a person is required;
`scripts/loop-dashboard.py` shows the board and the running loops as a live page;
`scripts/check.sh` and `scripts/lint-skills.py` check this repository against its
own rules, and `.githooks/` runs them before a commit.

## 0.4.0 and earlier

Not recorded here. The repository's git history is the record: `/merge` added, the
workspace environment detected, plugin marketplaces for both hosts.
