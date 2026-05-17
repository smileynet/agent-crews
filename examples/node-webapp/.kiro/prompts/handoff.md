---
name: handoff
description: "End-of-session handoff — delete old handoff doc, write a new one capturing current state for the next session."
---

Delete any existing `.scratch/HANDOFF.md`, then create a new one capturing everything the next developer (or session) needs to continue this work.

## Format

```markdown
---
created_at: 2026-05-17T15:04:00-04:00
base_commit: abc1234
handoff_key: replace-with-workstream-slug
---

# Handoff

## Objective
[What the receiving agent should accomplish next]

## Constraints
[Rules, boundaries, or things not to change]

## Prior Decisions
[Choices already made with brief rationale. Include rejected paths only when they prevent repeated dead ends]

## Current State
[Relevant files and artifact paths, current status, checks run / not run]

## Next Steps
[Ordered next actions, plus blockers or open questions if any]

## Evidence
[Optional: pointers to logs, test output, research notes, or other artifacts worth reading on demand]
```

## Rules
- Delete the old handoff first — a new handoff supersedes the prior one for the same `handoff_key`. Write the new file to `.scratch/HANDOFF.md`.
- `handoff_key` must be a short human-readable slug for the workstream (`auth-flow`, `release-0-3-0`, `repo-map`)
- `created_at` must be an exact ISO 8601 timestamp with offset
- `base_commit` must be the current `git rev-parse --short HEAD` value at handoff creation time
- Be specific — "fix the bug" is useless, "fix the timeout in eval-crew.py line 255 where intent_only evals still use global timeout" is useful
- Include file paths, function names, and artifact paths where relevant
- Point to evidence; do not paste large logs or transcript dumps into the handoff
- Keep it under 60 lines — dense, not verbose