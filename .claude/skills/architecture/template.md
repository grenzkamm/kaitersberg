# Architecture Template

Written to `docs/architecture.md`. Headings shown in English - write them in the
language of the project's documents.

---

```markdown
# Architecture

> How this product is built. One answer per question, so every feature is built the
> same way. Changing something here is a decision argued here, not an exception in
> one module.

## Module layout
<Folder tree with one line per level saying what belongs there.>

- **A module is:** <the unit - by domain, by layer, by feature>
- **A module may reach into:** <what - and what it may not>
- **Names:** <the convention a new file, class or function follows>

**Why:** <one or two sentences>

## The path of a request
1. <step> - <what it is responsible for>
2. …

**What each step must not do:** <the mistakes this ordering prevents>

## Tenant isolation
- **Enforced by:** <database policy | one shared data-access layer | …>
- **Enforced at:** <the single place>
- **A new query inherits it by:** <mechanism - not by the author remembering>
- **Deliberate exceptions:** <the ones that exist, and who may write them>

**Why:** <…>

## Permissions
- **Checked at:** <where the action happens>
- **Not checked at:** <the interface alone - hiding a button is not a protection>
- **Shape of a check:** <how it reads, in words>

## Business rules
- **Live in:** <…> - so they hold regardless of which entry point calls them
- **Do not live in:** <…>

## Validation
- **Untrusted input stops being untrusted at:** <the boundary>
- **Validated again at:** <where, or "nowhere, and here is why">

## Errors
| Kind of failure | Returns | User sees | Never in the message |
|---|---|---|---|

## Logging and audit
- **Logged:** <what, at which level>
- **Audited:** <which actions, with who and when>
- **Never in a log line:** <secrets, personal data, tokens - be specific>

## Background work
- **Runs outside a request:** <what>
- **Mechanism:** <…>   **Retries:** <how often, how spaced>
- **When it finally fails:** <what happens, who notices>

## Files and secrets
- **Uploads:** <where they go, how they are named, who may read them>
- **Secrets:** <where they live, how they reach the code, what never reaches the client>

## Migrations
- **Tool and naming:** <…>
- **Reversible?** <required | not required, and why>
- **Run when:** <…>   **Against real data:** <how it is rehearsed>

## Concurrent writes
- **Two people, one record:** <last write wins | version column, stale write refused | lock>
- **A stale page is refused by:** <mechanism - not by the author remembering>
- **The user sees:** <what, when their write is refused>

**Why:** <…>

## Data conventions
- **Time:** <stored as … , displayed in … , the boundary where it is converted>
- **Decimals and rounding:** <type, precision, where rounding happens, half-up or half-even>
- **Units:** <the canonical unit per quantity, and where conversion is allowed>
- **Identifiers:** <format, who generates them>

## Retention and deletion
| Entity or group | Delete means | Retained for | Enforced by |
|---|---|---|---|

- **Erasure request:** <what actually happens, and what legally survives it>

## Performance budgets
| Path | Budget | Measured by | Breach is noticed by |
|---|---|---|---|
| <normal page> | <p95 … ms> | | |
| <normal write> | <p95 … ms> | | |
| <the slowest thing this product does> | <…> | | |

- **Query rules:** <pagination default and maximum; no per-row query in a loop; the
  indexes that exist because a journey needs them>
- **Accepted for now:** <what is knowingly unmeasured, and until when>

## Testing
| Level | Covers | Database | Never mocked |
|---|---|---|---|
| Unit | | | |
| Integration | | | |
| End to end | | | |

- **Fixtures:** <how test data is made - and the rule that it comes from the spec's
  example data>
- **A test is named:** <the convention, including the AC number>

### Browser end to end
- **Runner:** <project-owned runner; use what already exists, otherwise choose one>
- **Runs locally:** `<exact command>`   **Runs in CI:** `<exact command>`
- **Starts the application:** <runner-managed web server | documented prerequisite>
- **Projects:** <the browser and viewport entries from docs/app-shell.md that run on
  every change, and any wider scheduled matrix>
- **State and authentication:** <how each test gets its own data, cookies and local
  storage; how the database is reset; how roles are authenticated>
- **Locators:** user-visible role, accessible name, label or text first; a test ID
  only when there is no stable user-facing contract; no CSS/XPath tied to layout
- **Waiting:** observable page or network state; no fixed sleeps
- **Retries and flakes:** <number locally and in CI>; the first failure is retained,
  and a test that passes only on retry is reported as flaky rather than green
- **Failure artefacts:** <trace, screenshot, console and failed requests; path and
  CI retention>
- **Visual regression:** <off | only for named screens with an approved baseline,
  projects and threshold>

## Quality gate
### Enforced by a machine
| Rule | Tool and setting | Threshold | Why |
|---|---|---|---|
| Formatting | | | |
| Linting | | <rule set; deliberately off: …> | |
| Types | | <strictness; forbidden escapes: …> | |
| Coverage | | **floor <n>%, may only rise** | |
| Browser E2E | | <which suite runs on each change> | |
| File / function size | | | |
| Module boundaries | | <who may import whom> | |
| Forbidden APIs and patterns | | | |

**The gate runs:** `<the exact commands, in order>` - after every batch in `/build`
and in CI.

**Git hooks** (versioned in the repository, installed by the documented setup command):

| Hook | Runs | Why not in the gate alone |
|---|---|---|
| `pre-commit` | <fast checks on staged files only> | catches it seconds after it was typed |
| `commit-msg` | <commit format from `CLAUDE.md`, or: not enforced> | nothing downstream ever reads a commit message |

`--no-verify` stays available and CI re-runs everything: the hook is the fast
correction, the gate is the proof.

**Suppressions** (`lint-disable`, type escapes, skipped tests) carry a reason on the
same line. One without a reason is a review finding.

### Left to judgement
<What no tool can see, written as an expectation so `/review` has something to
measure against.>
- <e.g. an abstraction needs a second caller before it exists>
- <e.g. a test must fail when the behaviour breaks - assert the behaviour, not the mock>
- <e.g. names come from docs/data-model.md, no synonyms>

## Dependencies
- **A new one needs:** <what counts as justification - and who decides>
- **Licences:** <acceptable | forbidden>
- **Versions:** <pinned exactly; lockfile committed>   **Updates:** <cadence and who>
- **Prefer over a dependency:** <the standard library and what is already installed>

## Conventions
<The short list a new file follows without asking: imports, exports, formatting,
comments, commit messages.>

## Decisions
| Decision | Alternatives | Why this one | What it costs later |
|---|---|---|---|

## Deliberately open
| Question | Waiting for | Decided by then at the latest |
|---|---|---|
```
