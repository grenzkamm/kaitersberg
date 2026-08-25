# How the work moves

This describes the process, not the paperwork: what happens at each stage, what it
receives, what it decides, and what it hands to the next one. The documents are
named only where they are the handover itself.

Two properties hold the whole thing together, and everything below is a consequence
of them:

- **The plan is the source of truth, and it lives in the repository.** Every stage
  reads what the previous one decided instead of asking the model to remember it. A
  session that starts three weeks later knows what a session from today knew.
- **Lifecycle rungs move forward once**, and the rung and owner are on the board.
  Review, QA, corrections and CI share the owned `In Review` delivery loop; its
  finer stage is persisted by the unattended runner.

```
Roadmap → Spec → Designed → Ready → In Progress → In Review → Done
                                                   ↺
                                      findings return to build inside
                                      the owned delivery loop
```

---

## Once per product

### Planning

**Receives** a briefing in prose - a paragraph, a document, a conversation.

**Decides** what the product is, who uses it, what it will not do, how the work is
cut into features, and in which order those can be built. The cut is the part that
matters: features are sized so that the ones in a wave can be built at the same time
without touching each other's files, and the first wave is pulled towards something
demonstrable rather than towards three weeks of authentication and empty tables.

**Hands over** a board of features, each a row with a scope line, a priority, its
dependencies and its wave - plus the documents every later stage reads: what the
product is, what the data means, who may do what, what the shell looks like.

**Requires a person once**, at the feature cut, before the rest is written. That is
the cheapest moment to disagree; everything downstream is derived from it.

### Architecture

**Receives** the plan.

**Decides** the house style once, so that nineteen features do not invent nineteen
answers: how a request travels, where tenant isolation is enforced, where business
rules live, how errors and logging work, how migrations run, what the test setup is,
and what the quality gate demands in numbers.

**Hands over** decisions that every later design cites. This is why it cannot be
rewritten casually: rewriting it invalidates every design that leaned on it.

**Requires a person** for two to four load-bearing choices, each presented with its
alternative and the cost of both.

### Scaffold

**Receives** the architecture.

**Decides** nothing new. It builds the repository that runs: services, migrations,
seed data, the test harness, the quality gate, continuous integration - and then
proves it from a clean state, so that the documented commands are true rather than
merely written.

**Hands over** a repository where the next stage can actually build something, and a
proof of what was run.

This is the only stage allowed to write configuration or start services. Everything
after it plans or builds features.

---

## Once per feature

Eight stages. Each one refuses to start when what it needs is missing, which is the
mechanism that keeps the pipeline honest: a stage that cannot proceed says so
instead of inventing the input it lacks.

### 1 · Specification

**Receives** one row from the board, and the plan documents around it.

**Decides** what the feature does in the language of its users: the stories, the
acceptance criteria as Given/When/Then, who may do what, which edge cases count,
what personal data is touched, and how each criterion will be tested.

**Hands over** criteria that are checkable. Everything downstream measures against
them: the design covers them, the tasks trace to them, the review expects them, the
test report gives each one a verdict.

**Requires a person** only when the scenario cut changes scope, introduces a
product decision or exceeds the review budget. Otherwise the approved roadmap is
enough authority and the summary is handed off without another wait.

**Refuses** when the project was never planned, and asks when the feature's
dependencies are not finished - speccing ahead is allowed, doing it silently is not.

### 2 · Technical design

**Receives** the specification.

**Decides** what will exist: every field with its type and rule, what is deliberately
not stored, what changes for each role, what the flow is in plain steps, what has to
migrate, and what the feature costs the parts that already exist. Written so that
somebody who does not read code can sign it.

**Hands over** the approved shape of the work - and it is approved explicitly, in
the document. Nothing downstream may start from a draft.

**Requires a person.** This is *the* checkpoint of the whole pipeline: the last
moment where changing your mind is cheap.

**Refuses** when there is no specification, and stops to ask when the specification
has open questions that would change the data or the roles.

### 3 · Task list

**Receives** the approved design.

**Decides** how the work is cut into half-day tasks, in which order they depend on
each other, and which of them can run at the same time. Tasks are grouped into
batches whose write sets are disjoint - that is what makes parallel work safe rather
than hopeful - and every task names the criterion it serves and how it is verified
on its own.

**Hands over** a plan of work that can be executed without further interpretation,
and the gate each batch has to pass before the next one starts.

**Refuses** when the design's approval block is empty, and warns when the design
still has open decisions: a task list built over an open decision produces rework in
exactly that spot.

### 4 · Build

**Receives** the task list.

**Decides** nothing that the plan already answered - and stops the moment reality
disagrees with it. It claims the feature on the board, works in its own isolated
copy of the repository, dispatches the tasks of a batch in parallel, and runs the
gate after each batch. Tests are written before the code and seen failing first: a
test that was never red proves nothing.

**Hands over** committed work, one commit per task, and a feature whose rung says it
is ready to be judged. Batch gates keep their full output in unique temporary files;
the integrated full gate leaves a schema-v2 `verification.json` plus bounded,
committed evidence extracts. `tested_sha` names the code that ran, and only the
evidence commit may follow it before review.

**Requires a person** only where the plan is silent. That is the rule that keeps an
agent from inventing behaviour: an invented behaviour is a defect that passes review,
because nobody specified otherwise.

**Refuses** when there is no task list, when the design was never approved, when
somebody else owns the feature, or when a dependency is not finished.

### 5 · Review

**Receives** the specification, the design and the diff - and nothing else. The
builder's account of the work is treated as a claim, not as evidence.

**Decides** whether what was built is what was approved. It forms its expectation
from the documents *before* opening the diff, because reading the code first makes a
reader explain the implementation instead of judging it.

**Hands over** findings, each with a location and a consequence, and a verdict. Only
two things block: the feature does not do what was approved, or it does something
that must not happen - data loss, a hole in the isolation, personal data where it
does not belong. Everything else is a note, and notes do not stop a feature.

**Runs in a session that did not build the feature.** A reviewer who watched it
being built shares the assumptions that produced its bugs.

**Fixes nothing.** A reviewer who fixes becomes an author and loses the only thing
that made them useful. In the unattended loop this is enforced: the session and its
parallel lanes receive a fixed read-only Git-query helper, not raw shell or the
mutating commands and shell aliases admitted by a broad `git *` permission.

### 6 · Quality assurance

**Receives** the built feature, the criteria it claims to satisfy and the build's
verification manifest. A green gate is reusable only at its `tested_sha`, or when
the remaining diff is exactly the committed manifest and bounded evidence; any
product, configuration or plan change makes it stale.

**Decides** whether the running system does what was promised: each criterion gets
its own verdict with evidence, the browser walk-through checks what only a screen
shows, the migration is run against data that already exists, and an adversarial
pass attacks the feature the way a hostile user would.

**Hands over** a report and a production-readiness verdict - and, when it fails, the
feature goes back to building.

This stage earns its cost by finding what the other two cannot. A defect can pass
the specification, pass the review and pass a green test suite, and still be visible
to anybody who looks at the screen for ten seconds.

**Fixes nothing**, for the same reason as the review: a tester who fixes can no
longer say what state the feature was in.

### 7 · Pull request

**Receives** everything the feature produced.

**Decides** nothing. It assembles: what was approved, what was built, what the review
and the test report said, what migrates, what configuration is new, and how a
reviewer can verify it by hand. Every claim traces to an artefact; a body claiming
green while a check is red teaches the next reviewer not to read yours.

**Requires a person** before pushing, because a pull request is outward-facing.

**Moves no rung.** The skill that writes the request cannot know whether anybody
accepted it.

### 8 · Merge

**Receives** an accepted pull request.

**Decides** the one irreversible thing in the pipeline, and therefore is started by a
person, never by a model.

**Hands over** a finished feature and a cleared field: the rung set to done, the
owner cleared, the branch removed, the isolated copy of the repository removed - and
a sentence naming which features just became available, because a finished
dependency is what unblocks the next work.

---

## When work comes back

The pipeline is not a straight line, and the return paths are as designed as the
forward ones.

| What happened | Where it goes | Why |
|---|---|---|
| The review requires changes | back to building, with the findings as the work list | The feature is not finished, so it is not judged again until it is |
| The test report says not production ready | back to building | Same rule, one stage later |
| Notes without a blocker | onward | Only two things block; everything else is recorded and does not stop the work |
| A defect found after the feature merged | the short path: reproduce, root cause, failing regression test, fix, request | It is a bug now, and a bug needs a reproduction, not a specification |
| A request arrives mid-flight | placed on the board with its true cost | The cost is which features it pushes back, named |
| Drift across the whole repository | filed as work, after a wave rather than after a feature | It is the divergence no single review can see, because no single review reads the whole thing |

After a return, the changed work is reviewed again in a fresh session. Review and
QA use their delta/retest modes when the blast radius is bounded; shared mechanisms,
migrations and permission boundaries escalate to a full pass.

---

## Where a person is required

Four planned places, and they are not negotiable:

1. **The feature cut**, at the end of planning.
2. **The load-bearing architecture decisions**, once per product.
3. **The design**, before anything is built from it.
4. **The merge**, which is the irreversible one. Pushing the request is the
   half-step before it, and is confirmed too.

The specification and task breakdown need no separate approval when they introduce
no decision and stay inside the approved scope and review budget. Everywhere else a person is *optional* - and where the documents are silent, the
agent stops and asks rather than choosing. That silence is a defect in the plan, and
answering it puts the answer back into the document so the next stage inherits it.

---

## Running it unattended

Building, reviewing and testing can run without anybody watching, one process per
stage - which is also what gives the review a session that did not build the
feature. It stops in exactly the places above: when the plan is silent, when the
rounds run out without a green result, and always before the merge.

What that does not change: the stages, their order, what each of them decides, and
who has to be asked. An unattended run is the same process with nobody in the chair.
