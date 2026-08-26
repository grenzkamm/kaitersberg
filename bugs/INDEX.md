# Bugs

| ID | What goes wrong | Severity | Status | Feature | Branch |
|---|---|---|---|---|---|
| BUG-1 | Codex invents an in-session delivery loop instead of using the runner | Major | Fixed | Delivery loop | muichdistl/fix-BUG-1-codex-loop-runner |
| BUG-2 | A hanging LOOP_NOTIFY blocks the delivery loop without timeout(1) | Major | Reproduced | Delivery loop | muichdistl/fix-loop-review-findings |
| BUG-3 | loop-status reports a same-named loop from another repository as running | Minor | Reproduced | Delivery loop | muichdistl/fix-loop-review-findings |
| BUG-4 | The status template still directs scope reads to spec.md | Minor | Reproduced | Status skill | muichdistl/fix-loop-review-findings |

Next free ID: BUG-5
