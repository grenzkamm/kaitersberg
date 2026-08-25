---
name: fix
description: Take one bug from report to merged fix - build a command that fails on it first, find the root cause rather than the symptom, write the failing regression test, fix it, verify, and open the pull request. Escalates to the feature pipeline when the fix turns out to be a change of behaviour.
---
<!-- Generated from .claude/skills/fix/ by scripts/port-to-codex.py.
     Do not edit: edit the source and regenerate. -->

# Fix

## Role
The feature pipeline is seven documents long because a feature is a decision
nobody has made yet. A bug is different: the decision was made, the code disagrees
with it. So this path is short - but it keeps the three things that actually
prevent a fix from causing the next bug: a loop that goes red on demand, a root
cause, and a test that fails first.

## Hard rules
- **No fix without a loop that goes red.** Not "I saw it happen once" - one
  command that fails on this bug, runs unattended, and will pass when it is fixed.
  If you cannot make it fail on demand, you cannot know you made it stop, and an
  unreproducible report gets written down and returned, not guessed at.
- **No hypothesis before the loop is red.** Reading the code to build a theory
  first is the failure this order exists to prevent: the first plausible cause
  looks right, so the real one never gets looked for.
- **Root cause, not symptom.** A report names one place; find every caller of what
  you are about to change. One guard in the shared function is a smaller diff than
  a guard in each caller - and patching only the path in the report leaves every
  sibling still broken.
- **The regression test fails before the fix.** Watch it go red for the right
  reason, then fix, then watch it go green. A test written after the fix proves the
  fix compiles.
- **Check the library against the version that is installed.** Both when you look
  for the cause and when you write the fix: the behaviour that changed between two
  versions is a common cause and an easy one to miss, and a fix written against a
  remembered API is the next bug. The version in the lockfile and the **Stack &
  versions** table in `docs/local-dev.md` say which documentation is the right one.
- **Fix the bug, nothing else.** Tidying you noticed on the way is either part of
  the cause or it is a separate change. Say which.
- **Escalate when it is not a bug.** If the "fix" changes what the product does,
  adds a field, changes who may do what, or touches more than a handful of files,
  it is a feature. Stop and route it to `$write-spec`; a behaviour change slipped in
  as a fix is how a specification quietly stops being true.

## Abort conditions
- The behaviour in the report matches the specification → this is not a bug, it is
  a change request. Say which document says so, and route to `$write-spec`.
- No specification covers it either way → the gap is upstream. Note it and ask.

---

## Phase 0 - Record it

```
🐛 Fix: BUG-n <short title>
```

Read `bugs/INDEX.md` and take the next `BUG-n`. If the file does not exist, create
it from the board skeleton in [template.md](template.md) - a board invented on the
spot is a board the next session has to guess at.
Write `bugs/BUG-n-<short-name>.md` from [template.md](template.md) with what is
known so far: what was expected, what happened, where, since when, who is affected,
how bad it is.

One file per bug. A bug that grows sub-documents was a feature.

## Phase 1 - Build the loop that goes red

Everything after this phase - tracing, hypotheses, the fix, the proof that it
worked - consumes one thing: a command that fails on this bug today and passes
once it is fixed. Build that first, and spend disproportionate effort on it. It is
the whole job; the rest is bookkeeping.

Ways to build one, in roughly the order they are cheap. Take the first that
actually reaches the bug:

1. A **failing test** at whatever level reaches it - unit, integration, end-to-end.
2. An **HTTP call** against the running dev server.
3. A **command-line run** with fixture input, diffed against known-good output.
4. A **browser script** that drives the interface and asserts on the page, the
   console or the network - Codex Browser, or the project's own browser tests.
5. A **captured artefact replayed**: a real request, payload or event log saved to
   disk and pushed through the code path in isolation.
6. A **throwaway harness**: the smallest slice of the system that reaches the code
   path in a single call, with everything else stubbed.
7. A **random-input loop**, when the bug is "sometimes the wrong answer".
8. A **bisection harness**, when it worked at a known earlier state - automate
   "start at state X, check, repeat" and let the version control do the search.
9. A **differential run**: the same input through two versions or two
   configurations, outputs diffed.
10. A **scripted walkthrough for a person**, when a human genuinely has to click.
    Last resort: the loop is then as slow and as forgetful as the person running it.

Then **tighten it**, because the loop is the tool you will use fifty times: make it
faster (skip unrelated setup, narrow the scope), sharper (assert the exact symptom,
not "it did not crash"), and deterministic (pin the clock, seed the randomness,
isolate the filesystem, freeze the network). A flaky thirty-second loop is barely
better than none; a deterministic two-second one finds the cause almost by itself.

**When it only happens sometimes**, the goal is not a clean reproduction but a
higher rate. Run the trigger a hundred times, in parallel, under load, with the
timing window narrowed. A bug that happens half the time is debuggable; one that
happens once in a hundred runs is not - raise the rate until it is.

This phase is done when you can name **one command you have already run**, and
paste its failing output, that is:

- **red on this bug** - it drives the real code path and asserts the symptom the
  report describes, so it can go green only when this bug is gone. Not "it runs".
- **deterministic** - the same verdict every run, or a pinned high rate.
- **fast** - seconds, not minutes.
- **runnable without a human** - anything else is not a loop, it is a chore.

Write the command and its failing output into the bug file.

**If you cannot build one**, stop and say so plainly: what you tried, what you
could not recreate, and what would settle it - access to the environment where it
happens, a captured artefact (log dump, network capture, a recording with
timestamps), or permission to instrument the running system. Do not proceed to a
theory. A speculative fix on an unreproducible report comes back with company.

Finally, **minimise**: shrink to the smallest scenario that is still red, cutting
input, callers, configuration and steps **one at a time** and re-running after each
cut. Done when removing any remaining piece turns it green - everything left is
load-bearing. That is a smaller space to search in Phase 2 and the regression test
in Phase 3.

## Phase 2 - Find the cause

Before touching anything, write down **three to five candidate causes, ranked**,
each with the prediction that could disprove it: *"if this is it, then changing X
makes the bug go away"*. A candidate you cannot make a prediction from is a feeling
- sharpen it or drop it. One hypothesis on its own anchors: it becomes the only one
considered, and it is right about half the time.

Show the ranked list to the user before testing it, if they are there. They know
things the code does not say - *"we changed number three last week"* - and re-rank
it in one sentence. Do not block on it; if nobody answers, work your own order.

Then test them against the loop, **one variable at a time**. Prefer a debugger or a
REPL where the environment has one; one breakpoint beats ten log lines. Where you
do add logging, tag every line with the same unique marker - `[DEBUG-a4f2]` - so
removing it afterwards is one search instead of a memory test. Never log everything
and grep.

Trace the path from the symptom to the decision that is wrong. Then, before
editing: **find every caller of the thing you are about to change** and decide
whether they have the same problem. Almost always they do - that is why the fix
belongs where they all pass through.

Write into the file: the cause in one sentence, the place, which other paths were
affected by the same cause, and which of your candidates it turned out to be - the
next person to read this learns more from the ranking than from the fix.

## Phase 3 - Test, then fix

1. Own worktree and branch: `fix/BUG-n-<short-name>`. Inside Orca
   (`ORCA_WORKTREE_ID` set, `orca` on the `PATH`) create it through the `orca-cli`
   skill so the app owns it; otherwise plain git.
2. Write the regression test from the minimised reproduction, named with the bug ID,
   **at a place where it exercises the real pattern that caused it**. A test one
   level too shallow - a single caller where the bug needed two, a unit test that
   cannot recreate the chain - passes and protects nothing. If there is no such
   place, that absence *is* a finding: note it in the bug file, say so in the pull
   request, and hand it to `$audit`. The code is shaped so that this bug cannot be
   locked down, which is a bigger problem than the bug.
3. Run it, watch it fail for the right reason. Record the failure. **Commit the red
   test on its own**: `test(BUG-n): reproduce <what happens>`. Two commits, test
   before fix, is what proves in the pull request that the test catches this bug -
   a test committed together with its fix has never been seen to fail.
4. Fix at the cause. Commit it separately: `fix(BUG-n): <what no longer happens>`.
5. Test green, then the full suite green - a fix that breaks two other tests has
   found a second bug, not solved one.
6. Re-run the Phase 1 loop against the original, un-minimised scenario. The
   minimised case going green proves the minimised case went green.
7. Check the neighbouring paths from Phase 2 are covered too.
8. Remove the instrumentation: search for the `[DEBUG-...]` marker until nothing is
   left, and delete the throwaway harness or move it somewhere it is clearly
   labelled as one. This is its own commit too - instrumentation that rides along in
   the fix commit is how a `[DEBUG-...]` line reaches production.

## Phase 4 - Verify beyond the test

- Walk the reproduction by hand, in the interface if that is where it appeared.
- If the bug touched data, check what happened to records already broken by it:
  are they repaired, still broken, or now inconsistent? **Existing damage is part
  of the fix**, and it is the part everybody forgets.
- If the bug was a hole in isolation, permissions or personal data: treat it as
  `$qa` would - probe the neighbouring paths too, and say what you found.

## Phase 5 - Close it

1. Complete `bugs/BUG-n-<short-name>.md`: cause, fix, test, damage to existing data,
   what else was checked.
2. `bugs/INDEX.md`: status to `Fixed`, with the branch - edited and committed in
   the default branch's checkout, not in the fix worktree. A status that travels
   with the branch is invisible until the branch merges, and the board is what the
   next session reads.
3. Open the pull request: title `fix(BUG-n): <what no longer happens>`, body from
   the bug file - reproduction, cause, fix, the test, existing damage, and how to
   verify it by hand. Confirm before pushing.
4. Ask it of every document the bug touched: **would somebody who reads only the
   documents now believe something false?** Where the answer is yes - the
   specification, the design or a plan document was wrong or silent - **correct it
   in the same pull request**. Where it is no, write *checked, nothing to change*
   and move on; a document edited on every fix stops being read. A fix that leaves
   the document wrong guarantees the bug returns as a feature.
5. Hand the merge and the cleanup to `$merge BUG-n`: it merges, verifies the work
   is in the target, removes worktree and branches, and sets `Closed`.

## Checklist
- [ ] A loop built that goes red on this bug - one command, run, output recorded
- [ ] The loop is deterministic, fast and runnable without a person
- [ ] Reproduction minimised: everything left in it is load-bearing
- [ ] Three to five ranked candidate causes written down before any was tested
- [ ] Cause found, not just the reported symptom, and which candidate it was recorded
- [ ] Library behaviour checked against the installed version, not a remembered one
- [ ] Every caller of the changed code checked for the same problem
- [ ] Regression test written first and seen failing, named with the bug ID
- [ ] Red test committed before the fix, instrumentation removal committed separately
- [ ] The test sits where it exercises the real cause - or its absence is filed for `$audit`
- [ ] The Phase 1 loop re-run against the original scenario, not only the minimised one
- [ ] Full suite green afterwards
- [ ] All `[DEBUG-...]` instrumentation and throwaway harnesses removed
- [ ] Records already damaged by the bug accounted for
- [ ] Nothing fixed beyond the bug, or the extra named as what it is
- [ ] Escalated to `$write-spec` if it turned out to be a behaviour change
- [ ] Documents corrected where the bug showed them wrong or silent
- [ ] Confirmed before pushing; nothing merged - `$merge BUG-n` does that and the cleanup
