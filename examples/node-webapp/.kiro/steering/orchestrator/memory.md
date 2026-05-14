---
inclusion: always
---
# Memory Protocol (Four-Tier)

## Tiers

| Tier | Location | Lifetime | Purpose |
|------|----------|----------|---------|
| Working | `.scratch/maps/` | Session | Scratchpad, intermediate results, maps |
| Session | `.scratch/session/` | Session | Current task state, decisions in progress |
| Episodic | `.kiro/memory/lessons.md` | Persistent | Lessons learned, patterns observed |
| Semantic | ADRs, steering, AGENTS.md | Permanent | Architectural knowledge, project rules |

## Write Rules
- **Working:** Write freely — this is your scratchpad
- **Session:** Write task state, partial results, context for handoff
- **Episodic:** Write when you learn something reusable (pattern, pitfall, shortcut)
- **Semantic:** Write only through formal processes (ADR, steering update, doc edit)

## Read Rules
- Check working memory first (cheapest, most current)
- Check episodic for relevant lessons before starting new work
- Check semantic for architectural constraints before proposing changes

## Aging
- Working: cleared between sessions (ephemeral)
- Session: cleared between sessions (ephemeral)
- Episodic: reviewed periodically, stale entries archived
- Semantic: permanent until explicitly superseded

## Discovery Mechanism
Knowledge scatters across: commits, comments, TODOs, threads, old docs.
When you encounter scattered knowledge:
1. Note where you found it
2. Propose where it should live (which tier)
3. Capture it in the appropriate location
4. Leave a breadcrumb at the original location if possible
