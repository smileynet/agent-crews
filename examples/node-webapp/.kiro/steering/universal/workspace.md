---
inclusion: always
---

# Workspace

Two project-scoped roots define where agents leave artifacts. Both are pre-created
during build; the contract is intentionally minimal.

| Root | Path | Lifecycle | Use for |
|------|------|-----------|---------|
| Ephemeral | `.scratch/` | ≤ one handoff cycle (newer handoff supersedes older) | Current handoff, scratch notes, draft artifacts |
| Durable | `.memory/` | Persists across sessions; promotion is explicit | Curated decisions, distilled findings, references worth keeping |

## Rules

- The standardized handoff lives at `.scratch/HANDOFF.md` (see `@handoff` / `@read-handoff`).
- Never write durable artifacts from inside the ephemeral root; promote intentionally.
- Treat ephemeral content as expendable — do not link to it from durable docs.
- All shared artifacts (anything another agent or future session may read) MUST start
  with a YAML frontmatter `created_at:` and `base_commit:`; handoffs additionally
  carry `handoff_key:`. Private scratch you alone will read is exempt.
