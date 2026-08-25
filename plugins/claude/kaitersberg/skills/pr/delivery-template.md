# Delivery Finding Template

Written to `features/PROJ-x-<short-name>/delivery.md`. It is the current handoff,
not an accumulating CI transcript; Git retains old versions.

```markdown
# PROJ-x - Delivery

**Head:** <sha>   **Target:** <branch@sha>   **State:** CI failed | Conflict | Resolved

## Current finding
- **Check or conflict:** <name>
- **Evidence:** <URL or captured log path and decisive line>
- **Consequence:** <what failed or cannot merge>
- **Smallest proof of resolution:** <test or clean merge plus gate>

## Resolved
<empty while current; after green, one line naming the resolving SHA>
```
