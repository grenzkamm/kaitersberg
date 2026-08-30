# How the work moves

This describes the process, not the paperwork: what happens at each stage, what it
receives, what it decides, and what it hands to the next one. The documents are
named only where they are the handover itself.

The same thing as one picture, including every file each stage touches:
[workflow.excalidraw](workflow.excalidraw), or [workflow-de.excalidraw](workflow-de.excalidraw)
in German.

Kaitersberg owns the first three stages. Everything after them is done by skills
from outside this framework, and they are described here too, because a process
that stops where the tooling changes hands is not a process.

Two properties hold the whole thing together, and everything below is a consequence
of them:

- **The plan is the source of truth, and it lives in the repository.** Every stage
  reads what the previous one decided instead of asking the model to remember it. A
  session that starts three weeks later knows what a session from today knew.
- **Lifecycle rungs move forward once**, and the rung and owner are on the board.
  Test, review, corrections and CI share `In Review`, so findings do not bounce the
  board.

```
Roadmap → Spec → Ready → In Progress → In Review → Done
                                        ↺
                             findings return to the build
                             without moving the rung back
```

The three rungs around the build belong to the human, because the build belongs to
the human. Kaitersberg plans a product and stands it up; the code is written and
judged elsewhere.

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

**Hands over** decisions that every later specification cites. This is why it cannot
be rewritten casually: rewriting it invalidates everything that leaned on it.

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

This is the only stage allowed to write configuration or start services. It is also
the last stage Kaitersberg performs.

---

## Once per feature

Six stages, none of them Kaitersberg's. What they read is what the three stages
above wrote, and each one refuses to start when what it needs is missing: a stage
that cannot proceed says so instead of inventing the input it lacks.

### 1 · Alignment

`mattpocock:grilling`

**Receives** one row from the board and whatever you have in your head about it.

**Decides** nothing on its own. It asks, one question at a time, and waits for each
answer, until you and the agent mean the same feature. Where a fact can be looked up
in the repository it looks it up instead of asking; the decisions it puts to you.

**Hands over** a shared understanding, and nothing written. This stage exists because
the most common failure in software is not a bad implementation, it is a good
implementation of the wrong thing.

**Skip it** for a feature the plan already answers completely. Reach for it whenever
the plan documents are silent about what you actually want, which is most features
after the first wave.

### 2 · Specification

`agent-skills:spec`, told to write into `features/PROJ-x-<name>/spec.md`

**Receives** the board row, the plan documents around it and the alignment above.

**Decides** what the feature does in the language of its users: the stories, the
acceptance criteria as Given/When/Then, who may do what, which edge cases count,
what personal data is touched, and how each criterion will be tested.

**Hands over** criteria that are checkable. Everything downstream measures against
them: the tasks trace to them, the review expects them, the test report gives each
one a verdict.

**Refuses** when the project was never planned, and asks when the feature's
dependencies are not finished - speccing ahead is allowed, doing it silently is not.

### 3 · Release

You, by hand.

**Receives** the specification.

**Decides** whether it may be built. This is *the* checkpoint of the whole process:
the last moment where changing your mind is cheap. Nothing downstream may start from
a draft.

**Hands over** two lines nobody else writes: `status: ready` and `verified` in the
specification's frontmatter, and `Ready` on the board. A checkpoint that a skill can
set itself is not a checkpoint.

### 4 · Task list

`agent-skills:plan`, told to write into `features/PROJ-x-<name>/tasks.md`

**Receives** the released specification.

**Decides** how the work is cut into small tasks, in which order they depend on each
other, and which of them can run at the same time. Every task names the criterion it
serves and how it is verified on its own, and the batch gate from the architecture
is copied in as the check each group has to pass.

**Hands over** a plan of work that can be executed without further interpretation.

### 5 · Build

`agent-skills:build auto`, given both paths

**Receives** the task list.

**Decides** nothing that the plan already answered - and stops the moment reality
disagrees with it. It claims the feature on the board, works in its own isolated
copy of the repository, and runs the gate as the task list tells it to. Tests are
written before the code and seen failing first: a test that was never red proves
nothing.

**Hands over** committed work, one commit per task, and a feature whose rung says it
is ready to be judged.

**Requires a person** only where the plan is silent. That is the rule that keeps an
agent from inventing behaviour: an invented behaviour is a defect that passes review,
because nobody specified otherwise.

### 6 · Judgement

`agent-skills:test`, then `review`, then `ship` - in a session that did not build it

**Receives** the specification and the diff. The builder's account of the work is
treated as a claim, not as evidence.

**Decides** whether what was built is what was released. The review forms its
expectation from the documents *before* opening the diff, because reading the code
first makes a reader explain the implementation instead of judging it. The test pass
gives every acceptance criterion a verdict against the running system. The ship pass
turns both into a go or no-go with a rollback plan.

**Hands over** findings, each with a location and a consequence, and a verdict. Only
two things block: the feature does not do what was released, or it does something
that must not happen - data loss, a hole in the isolation, personal data where it
does not belong. Everything else is a note, and notes do not stop a feature.

**Runs in a session that did not build the feature.** A reviewer who watched it
being built shares the assumptions that produced its bugs.

**Fixes nothing.** A reviewer who fixes becomes an author and loses the only thing
that made them useful.

### 7 · Pull request and merge

`gh pr create`, then `superpowers:finishing-a-development-branch`

**Receives** everything the feature produced.

**Decides** nothing at first. The request assembles: what was released, what was
built, what the review and the test report said, what migrates, what configuration
is new, and how a reviewer can verify it by hand. Every claim traces to an artefact;
a body claiming green while a check is red teaches the next reviewer not to read
yours.

Then the merge decides the one irreversible thing in the whole process, and is
therefore started by a person, never by a model.

**Hands over** a finished feature and a cleared field: the rung set to `Done`, the
owner cleared, the branch removed, the isolated copy of the repository removed - and
a sentence naming which features just became available, because a finished
dependency is what unblocks the next work.

---

## When work comes back

The process is not a straight line, and the return paths are as designed as the
forward ones.

| What happened | Where it goes | Why |
|---|---|---|
| The review requires changes | back to the build, with the findings as the work list | The feature is not finished, so it is not judged again until it is |
| The test pass says not production ready | back to the build | Same rule, one stage later |
| Notes without a blocker | onward | Only two things block; everything else is recorded and does not stop the work |
| A defect found after the feature merged | `mattpocock:diagnosing-bugs`, then a failing test before any fix | It is a bug now, and a bug needs a reproduction, not a specification |
| A request arrives mid-flight | placed on the board with its true cost | The cost is which features it pushes back, named |
| The branch collides with the default branch | `mattpocock:resolving-merge-conflicts`, before the pull request | Always resolve, never abort. Each side has a reason, and the reason is in that feature's own spec |

After a return, the changed work is reviewed again in a fresh session.

---

## Where a person is required

Four planned places, and they are not negotiable:

1. **The feature cut**, at the end of planning.
2. **The load-bearing architecture decisions**, once per product.
3. **The release of a specification**, before anything is built from it.
4. **The merge**, which is the irreversible one. Pushing the request is the
   half-step before it, and is confirmed too.

Everywhere else a person is *optional* - and where the documents are silent, the
agent stops and asks rather than choosing. That silence is a defect in the plan, and
answering it puts the answer back into the document so the next stage inherits it.
