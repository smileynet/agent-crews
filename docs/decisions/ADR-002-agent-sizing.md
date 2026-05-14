# ADR-002: Agent Sizing — When to Split

**Status:** Accepted  
**Date:** 2026-05-06  
**Sources:** OpenAI Practical Guide, NimbleBrain, BuilderHub, AutonomousAICapabilities

## Context

Need clear criteria for when a single agent should become multiple agents.

## Decision

### Split Signals (any one = split)

| Signal | Threshold |
|--------|-----------|
| Context overflow | Prompt > 80 lines or > 15 tools |
| Domain conflict | Two contradicting DO NOT rules |
| Tool overload | > 10-15 tools, especially overlapping |
| Role confusion | Agent produces output for wrong audience |

### Where Guidance Lives

| Content Type | Location | Loaded |
|-------------|----------|--------|
| Identity + routing | Agent prompt | Always |
| Behavioral rules | Steering files (via components) | Always (per agent type) |
| Domain knowledge | Skills | On keyword trigger |
| Project conventions | Steering (project.md) | Always |

### Context Budget Rule

Total agent context (prompt + steering + triggered skills) should stay under 4000 tokens for workers, 6000 for orchestrators. Beyond this, quality degrades measurably.

## Consequences

- Crew YAMLs keep agent prompts short (identity + specialization only)
- Behavioral rules live in components (shared, not duplicated per agent)
- Skills are focused and small (< 100 lines each)
- When an agent accumulates too many concerns → split into two agents
