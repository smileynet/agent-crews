---
name: task-lifecycle
description: Use when managing multi-task work with phase tracking. Adds phase prefixes to todo_list items for visibility.
---

# Task Lifecycle Phases

When managing multiple tasks, prefix todo_list items with their current phase:

```
[research] Investigate root cause of BUG-9
[design] Plan fix approach for name_prefix
[build] Apply fix to 7 IAM roles
[test] terraform validate + plan
[review] Check for regressions
[done] Committed and pushed
```

## Phase Transitions

Update the prefix when work moves forward:
- `[research]` → researcher/tracker/scout has findings
- `[design]` → architect/strategist/tactician has a plan
- `[build]` → paladin/hunter/scv is implementing
- `[test]` → shaman/carver/observer is validating
- `[review]` → inspector/tonberry is checking
- `[done]` → mark complete in todo_list

## Status Reporting

When user asks "what's the status?", group by phase:
```
## Status
- [done] BUG-1: fixed name_prefix in teamcity
- [test] BUG-9: fix applied, running validate
- [research] BUG-11: investigating S3 policy issue
- [blocked] BUG-5: needs GHCR credentials
```
