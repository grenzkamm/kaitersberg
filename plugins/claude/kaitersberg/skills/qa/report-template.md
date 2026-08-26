# QA Report Template

Written to `features/PROJ-x-<short-name>/qa.md`, beside `spec.md`, `design.md`,
`tasks.md` and `review.md`. Screenshots, recordings and captured output go into
`features/PROJ-x-<short-name>/evidence/` and are linked relatively. Headings shown in English -
write them in the language of the specification.

---

```markdown
# PROJ-x: <Feature name> - Test report

**Tested:** YYYY-MM-DD   **Branch:** feature/PROJ-x-<name>   **Commit:** <sha>
**Mode:** Full | Targeted from <previous tested sha>   **Scope reason:** <why this is sufficient>
**Build evidence:** `verification.json` tested <sha> · HEAD equal | evidence-only descendant
**Environment:** <local | staging>   **Base URL:** <url>   **Application/build:** <version>
**Database:** <state and reset command/run>   **Test data:** <fixtures>, <n> tenants, <roles>
**Automated browser:** <runner and version>   **Projects:** <browser + viewport list>
**Agentic walkthrough:** <tool and version>   **Browser/viewport:** <actual values>

## Verdict
**Production ready | Ready with reservations | Not production ready**

<Two or three sentences. If it is not ready, name the one finding that decides it.>

| Severity | Count |
|---|---|
| Critical | |
| Major | |
| Minor | |
| Cosmetic | |

## Acceptance criteria
| AC | What it requires | Level | Verdict | Evidence |
|---|---|---|---|---|
| AC-1 | <one line> | Integration | Passed | `<test name>` green at <sha> |
| AC-2 | | E2E | Failed | F-1 |
| AC-3 | | Manual | Not automatically testable | Screenshot `evidence/ac-3.png` |

<Every AC of the spec has a row. Blocked counts as not passed.>

## Automated levels
| Suite | Command | First run | Final result | Numbers / retries | Evidence |
|---|---|---|---|---|---|
| Unit | | | | <n> passed, <n> failed | |
| Integration | | | | | |
| Browser E2E | | | | <n> passed, <n> failed, <n> flaky | <report/trace paths> |
| Lint / types | | | | | |

**Flakes:** <none | test, first failure, retry that passed, finding. A retry-only
pass is not reported as clean.>

**Tests probed:** <which behaviours were broken on purpose, and whether the test
went red. A test that stayed green is a finding.>

## Agentic browser walkthrough
| Step | Role | Project / viewport | Expected | Observed | Console / network | Evidence |
|---|---|---|---|---|---|---|

- **Empty state:** <what was shown before any data existed>
- **Loading / error states:** <observed>
- **Texts:** <matched the spec's text table | the deviations>
- **Formats:** <numbers, dates, amounts - as specified?>
- **Keyboard:** <whole flow reachable? where focus landed after save and after error>
- **Accessibility semantics:** <roles, accessible names, status/error announcements>
- **Reflow:** <required narrow viewport and 200% zoom, or not applicable with reason>
- **Recording:** <optional path, or "not recorded">

## Migration
| What | Result |
|---|---|
| Ran against existing data | <rows before, duration, outcome - or "no migration in this feature"> |
| Existing rows afterwards | <filled, defaulted, empty - and whether the feature works for them> |
| Reversibility | <rolled back and forward ✓ | not required by the architecture | data lost: …> |

## Performance
| Path | Budget (`docs/architecture.md`) | Measured | Volume |
|---|---|---|---|

## Edge cases
| Case | Expected | Observed | Verdict |
|---|---|---|---|

## Adversarial pass
| Probe | What was tried | Result | Assessment |
|---|---|---|---|
| Tenant isolation | Tenant A read/changed/deleted an ID of tenant B, interface and API; did the error reveal the record exists | | |
| Broken access control | Every operation as each refused role, bypassing the interface, plus a try to grant oneself a role | | |
| Unauthenticated | Every route with no session | | |
| Injection through storage | Payloads in free text, then viewed in <screen, print, export, mail> | | |
| Input abuse | Wrong types, negatives, huge values, long strings, wrong and oversized files | | |
| Repetition | <n> requests - did the limit hold at its number, what was shown, was it recorded | | |
| Enumeration | Message and timing for "does not exist" vs "not yours" | | |
| Personal data leaking | Logs, audit records, error responses, outgoing calls | | |
| Client-side trust | Browser-side check bypassed | | |

<A probe that broke nothing is still a row. That is what makes the report worth
believing.>

## Findings
### F-1 - <title> · Critical | Major | Minor | Cosmetic
- **Breaks:** AC-n | <security rule> | <design section>
- **Reproduce:** <exact steps with the example data>
- **Expected:** <from the spec>
- **Observed:** <what happened, with the actual output>
- **Evidence:** <command output, screenshot, console line>
- **Consequence:** <what it costs in production>

## Not tested
| What | Why | Risk of leaving it |
|---|---|---|

## Next
- Not production ready → keep the owned feature `In Review`; `/build` works these
  findings, then `/review` in a fresh session, then replace this current report.
- Otherwise → `/pr`.
```
