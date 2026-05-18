# ADR-001: Crew Design Constraints from Prior Art

**Status:** Accepted  
**Date:** 2026-05-06  
**Sources:** Construction Crew, Artist Crew, Pulitzer Crew, Figma Crew, PACE PA, Sprint AI Agent, AgentDevStudioKit

## Context

Studied 6+ multi-agent implementations to extract what works and what fails.

## Decisions

### Structural Constraints

1. **Orchestrator/worker split is mandatory.** Three archetype types: `dispatcher` (depth 0, dispatches to crew leads), `orchestrator` (depth 1, dispatches to workers), `worker` (depth 2, executes, cannot spawn agents). Max 3 levels deep. Tool permissions enforce the hierarchy.
2. **Start with 5 agents, add when you feel pain.** Every over-engineered crew (15+ agents) had velocity problems. Smaller = better until proven otherwise.
3. **Tool permissions are enforcement; prompts are suggestions.** If something is forbidden, remove it from `allowedCommands`. Never rely on prompt-only restrictions.
4. **Progressive disclosure for skills.** Don't load everything at session start. Skills trigger on keywords. Context files load eagerly only when always-needed.

### Workflow Constraints

5. **Research before design, design before implementation.** Every successful system enforces this sequence. Skipping research leads to rework.
6. **Criteria = outcomes, not scripts.** "Stack reaches CREATE_COMPLETE" not "run `aws cloudformation deploy`." Workers are autonomous.
7. **Atomic, committable changes.** Each task produces one focused change that can be committed independently.
8. **Verification is mandatory, not optional.** Every implementation must run build/test before marking complete. "Looks right" is not verification.

### Antipatterns (hard constraints — never do these)

9. **No god agents.** One agent doing everything = quality collapse.
10. **No lateral or upward delegation.** Dispatchers → orchestrators only. Orchestrators → workers only. Workers never delegate. Orchestrators cannot dispatch to other orchestrators. Validated at build time.
11. **No open-ended questions.** Research first, propose with evidence. Don't put cognitive load back on the human.
12. **No editing generated files.** Source of truth is crew.yaml + components. Generated .json is ephemeral.
13. **No monolithic skills.** Each skill < 100 lines, focused on one concern.
14. **No template copy drift.** Use generation/overlay, not copy-paste.

## Consequences

These constraints are encoded in:
- Component architecture (behavioral rules in components, not crew prompts)
- Generator design (source → generated, never edit output)
- Agent tool permissions (allowedCommands as enforcement)
- Verification component (gate workflow mandatory for all task types)

## Amendment: 3-Level Hierarchy (2026-05-15)

### What Changed

The original 2-level constraint (orchestrator → worker) was expanded to a 3-level hierarchy (dispatcher → orchestrator → worker). The single-orchestrator model couldn't scale across multiple crews in a single project — the orchestrator's routing table grew too large and context budget was consumed by routing logic rather than useful work.

### Validation

Tested in `~/code/depth-test` (2026-05-15). A dispatcher routing to crew-specific orchestrators reduced per-agent context overhead by ~40% and eliminated cross-crew routing errors entirely.

### Three Archetype Types

| Depth | Type | Role | Tools |
|-------|------|------|-------|
| 0 | `dispatcher` | Routes to crew leads based on intent | `subagent` only |
| 1 | `orchestrator` | Decomposes tasks, delegates to workers within its crew | `subagent` only |
| 2 | `worker` | Executes tasks, produces artifacts | Domain tools, no `subagent` |

Rules:
- Dispatchers cannot do work — they only route
- Orchestrators cannot dispatch to other orchestrators
- Workers cannot spawn agents
- Direction is strictly downward: no lateral or upward delegation

### Build-Time Enforcement

`generate.py` validates the hierarchy at generation time:
- Each agent's `depth` field must match its archetype type
- Agents with `subagent` tool must be depth 0 or 1
- Agents at depth 2 cannot have `subagent` in their tool list
- Cross-crew orchestrator references are flagged as errors
