# ADR-009: Shared Utility Agents

**Status:** Accepted
**Date:** 2026-05-15

## Context

The component system generates steering that references utility agents (verifier, editor) which orchestrators should dispatch. However, these agents were either:
1. Not generated at all (component generation bug, now fixed)
2. Generated but not wired into orchestrators' `availableAgents`
3. Defined in one crew (bug-fix defines verifier) but inaccessible to other crews' leads

The auto-scoping rule ("orchestrators see only their own crew's workers") is correct for domain-specific workers but wrong for cross-crew utilities that any lead needs.

## Decision

**Agents marked `shared: true` are accessible to all orchestrators in the project.**

### Mechanism

In crew YAML:
```yaml
agents:
  - name: verifier
    shared: true
    # ... rest of definition
```

Generator behavior:
1. Generate all crew agents normally (shared agents live in their home crew)
2. After all crews are generated, collect names of all `shared: true` agents
3. Inject shared agent names into every orchestrator's `availableAgents` and `trustedAgents`
4. The auto-generated dispatcher also gets shared agents in its routing

### Deduplication with Component Subagents

Components (narration, writing) also define subagents (verifier, editor). When both a crew-defined shared agent and a component subagent have the same name:
- The crew-defined version wins (it's richer — has skills, resources, domain prompt)
- The component subagent is skipped (not written if file already exists)

### Which Agents Are Shared

| Agent | Home Crew | Why shared |
|-------|-----------|-----------|
| verifier | bug-fix | Completion protocol requires independent verification |
| editor | research | Writing protocol requires prose review |
| kiro-helper | meta | CLI troubleshooting useful to any lead |

Shared agents are the exception, not the rule. Most agents are crew-specific workers.

## Alternatives Considered

- **Component subagents only.** Rejected — component versions are minimal (read + shell). Crew-defined versions have skills and domain-specific prompts. Projects with the bug-fix crew should get the richer verifier.
- **All agents accessible to all orchestrators.** Rejected — defeats the purpose of crew scoping. Leads should focus on their domain.
- **Merge component + crew definitions.** Rejected — adds complexity for no clear benefit. Skip-if-exists is simpler.

## Consequences

- Orchestrators can follow steering instructions that reference verifier/editor
- The completion protocol ("dispatch verifier before DONE") actually works
- Adding `shared: true` to an agent is a one-line change with project-wide effect
- Shared agents appear in every lead's routing table (may add noise if overused)
