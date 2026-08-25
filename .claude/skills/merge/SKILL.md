---
name: merge
description: Merge one finished feature's pull request and clean up everything it leaves behind - the worktree, the local and remote branch, the board, and whatever the environment still thinks is open. Sets the feature to Done. Writes no code.
argument-hint: "PROJ-x or BUG-n"
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Edit, Glob, Grep, Bash, Skill, AskUserQuestion
model: opus
---

# Merge

## Role
The pull request is open, reviewed and tested. You merge it and leave nothing
behind: no worktree, no branch, no row on the board that still claims somebody is
working on this.

**A person starts this and no model calls it by itself.** Merging is the one
irreversible step in the pipeline, and it is the user's decision - every other skill
here can be re-run, this one cannot be un-run.

## Hard rules
- **Never merge on a red check or an open verdict.** CI green, `review.md` not
  `Changes required`, `qa.md` not *Not production ready* - or, for the foundation
  feature, its `proof.md` and its review. A merge is where a red check stops being
  cheap.
- **Confirm before merging.** Show the feature, the pull request, the target branch,
  the check results and the merge strategy, then wait. Outward-facing and final.
- **Cleaning up is part of merging, not a favour afterwards.** A branch that merged
  three weeks ago and still has a worktree is how a repository becomes a graveyard
  nobody dares to sweep.
- **Never force anything away.** A worktree that refuses to go has uncommitted work
  in it; that is a finding, not an obstacle. The one exception is `git branch -D`
  after a confirmed squash or rebase merge, where the target carries the changes but
  not the commits - see Phase 3.
- **Verify the merge before you clean.** Deleting a branch because a merge command
  exited zero is how work disappears; check the target branch actually contains it.
- **One feature.** Never merge two pull requests "while you are in there".
- **A bug fix merges the same way.** `/fix` leaves a `fix/BUG-n-…` branch and a row
  in `bugs/INDEX.md`; everything below applies, with `Closed` as the rung instead of
  `Done` and the bug file in place of spec and test report.

## Abort conditions
- The feature is not `In Review` in `features/INDEX.md` → say what state it is in.
- No pull request, or it is closed rather than merged → point at `/pr`.
- `review.md` says `Changes required`, or `qa.md` says *Not production ready* → the
  feature belongs back in `/build`, not in the target branch.
- CI is red or still running on the head commit → wait or fix; do not merge past it.
- The branch has uncommitted or unpushed work → commit and push it first, or the
  merge silently leaves it out.

---

## Phase 0 - Check what is actually true

```
🔗 Merge: PROJ-x [name]
```

1. `features/INDEX.md`: status, owner, branch.
2. The verdicts: `review.md` and `qa.md` - or `proof.md` and `review.md` for the
   foundation feature `PROJ-1`.
3. The pull request and its checks, with the forge's own tool: `gh pr view` and
   `gh pr checks` on GitHub, `tea pr` on Forgejo or Gitea, whatever the remote
   actually is. No tool for this forge means the user merges in the web interface
   and you verify afterwards - say so rather than guessing a command.
4. The worktree: `git status` in it, and `git log <target>..HEAD` - nothing
   uncommitted, nothing unpushed.
5. No active unattended loop owns the feature: the lock under the Git common
   directory's `kaitersberg/loops/` directory is absent. A live lock means merge
   must wait; never clean state out from underneath a running loop.

## Phase 1 - Confirm, then merge

Show it and wait:

```
PROJ-x [name] → <target branch>
Pull request: <url>   Commits: N   Diff: +A −B across C files
Review: <verdict>   QA: <verdict>   CI: <checks and results>
Strategy: <merge | squash | rebase - whichever this repository uses>

Merge this?
```

Take the merge strategy from what the repository already does rather than a
preference: look at the target branch's history. A repository that squashes
everything does not want one merge commit from you, and the commits `/build` shaped
per task survive only where the repository keeps them.

On yes, merge with the forge's tool. On no, stop and change nothing.

## Phase 2 - Verify it landed

Fetch the target branch and confirm the change is in it - the pull request reports
`merged`, and the target's history contains the work (`git log <target> --oneline`,
or the merge commit, or the squashed commit). **Only now is the branch expendable.**

If the merge did not happen - a protection rule, a conflict that appeared between
check and merge, a permission - report exactly that and stop. A conflict here goes
back to `/build`, which merges the target in and re-runs the gate; it is not
resolved in a hurry at the merge button.

## Phase 3 - Clean up locally

In this order, because each step checks the one before it:

1. Leave the worktree: move the session back to the main working tree, so nothing
   holds the directory you are about to remove.
2. Update the main tree: `git checkout <target>` and pull, so the local target
   actually contains what you just merged.
3. Remove the worktree. Inside Orca (`ORCA_WORKTREE_ID` set, `orca` on the `PATH`)
   through the `orca-cli` skill - whatever created it removes it; otherwise
   `git worktree remove .worktrees/PROJ-x-<short-name>`. Refuses to go means
   uncommitted work: stop and report it.
4. Delete the local branch: `git branch -d feature/PROJ-x-<short-name>`. After a
   squash or rebase merge this fails although the work is in - the target has the
   changes, not the commits. With Phase 2 confirmed, `-D` is correct and is not a
   force.
5. Delete the remote branch if the forge did not: `git push origin --delete
   feature/PROJ-x-<short-name>`. Then `git remote prune origin` and
   `git worktree prune`, which clear the entries that outlive their directories.
6. After the worktree and both branches are gone, remove the completed feature's
   persisted loop-state JSON from the Git common directory's
   `kaitersberg/loops/` directory. Keep archived reset states; they are diagnostic
   evidence. Never override an active lock to do this cleanup.

## Phase 4 - Update the board

1. `features/INDEX.md`: status `In Review` → **`Done`**, **owner cleared**, branch
   column emptied. For a bug: `bugs/INDEX.md` to `Closed`. That single edit is what unblocks every feature depending on
   this one; a `Done` row that still names an owner reads as "someone is on it".
2. Name which features just became pickable by the pick rule - dependencies now
   `Done`, no owner, nothing serialized before them in their wave. That is the
   sentence the next session or loop acts on.
3. Commit the board change on the default branch, where you already are and where
   every board edit belongs: `docs(PROJ-x): Set PROJ-x to Done after the merge`.

## Phase 5 - Report

```
## PROJ-x - [name] merged

**Merged:** <url> → <target> as <merge | squash | rebase>, <commit>
**Cleaned:** worktree removed · local branch removed · remote branch <removed | already gone>
**Board:** PROJ-x `Done`, owner cleared
**Now pickable:** PROJ-y, PROJ-z - <or "nothing new; the next wave still waits on …">
**Left behind on purpose:** <anything not cleaned, and why - or "nothing">

Next: `/write-spec PROJ-y`.
```

## Checklist
- [ ] Feature was `In Review`, with both verdicts allowing the merge
- [ ] CI checked on the head commit, not on an older one
- [ ] Nothing uncommitted or unpushed in the worktree before merging
- [ ] Merge strategy taken from the repository's own history
- [ ] User confirmed before the merge
- [ ] Merge verified in the target branch's history before anything was deleted
- [ ] Worktree removed by whatever created it; never forced
- [ ] Local and remote branch removed; `remote prune` and `worktree prune` run
- [ ] No active loop lock was overridden; completed loop state removed only after branch cleanup
- [ ] `features/INDEX.md`: `Done`, owner cleared, branch column emptied - or `bugs/INDEX.md`: `Closed`
- [ ] Features that became pickable named
- [ ] Nothing else merged, nothing else deleted
