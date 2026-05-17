---
name: read-handoff
description: "Start-of-session — read the handoff doc from the previous session and orient yourself."
---

Read `{{workspace.ephemeral}}/HANDOFF.md` and orient yourself to continue the work.

## After reading, report:
1. The `handoff_key`, `created_at`, and `base_commit`
2. The objective in one sentence
3. The active constraints
4. The current state (what exists now, including files/artifacts and verification status)
5. The first 1-2 next steps you would take
6. Whether any evidence pointers should be read before acting

Treat the handoff as point-in-time state, not durable truth. If the repo has changed materially since `base_commit`, say so before proceeding.
