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

## Discovery
When you encounter scattered knowledge (commits, TODOs, old docs):
1. Capture it in the appropriate tier
2. Leave a breadcrumb at the original location
