---
name: handoff
description: "End-of-session handoff — delete old handoff doc, write a new one capturing current state for the next session."
---

Delete any existing `scratch/HANDOFF.md`, then create a new one capturing everything the next developer (or session) needs to continue this work.

## Format

```markdown
# Handoff — [date]

## What was being worked on
[1-3 sentences: the task/goal]

## Current state
[What's done, what's in progress, what's blocked]

## Key decisions made
[Bullet list of decisions that affect next steps]

## Files modified
[List of files changed in this session]

## Next steps
[Ordered list of what to do next — specific and actionable]

## Context the next session needs
[Anything non-obvious: gotchas, failed approaches, open questions]
```

## Rules
- Delete the old handoff first (it's stale)
- Be specific — "fix the bug" is useless, "fix the timeout in eval-crew.py line 255 where intent_only evals still use global timeout" is useful
- Include file paths, function names, line numbers where relevant
- If an eval run or build is in progress, note it
- Keep it under 50 lines — dense, not verbose
