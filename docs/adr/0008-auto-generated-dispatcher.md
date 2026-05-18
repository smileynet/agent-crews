# ADR-008: Auto-Generated Project Dispatcher

**Status:** Accepted
**Date:** 2026-05-15

## Context

The 3-level agent hierarchy (dispatcher → lead → worker) was introduced as the standard architecture for all deployed projects. However, the dispatcher was defined inside the meta crew YAML and deployed verbatim to target projects — meaning every project got a dispatcher that talked about "the agent-crews repo" and routed to meta crew agents (crew-creator, crew-doctor) instead of the project's actual crew leads.

This violated the architecture's own principles:
- The dispatcher should route to the project's leads (general-lead, bugfix-lead, etc.)
- Each crew defines its lead + workers, not a dispatcher
- The dispatcher is a project-level concern, not a crew-level one

Session analysis showed 97% of work in the agent-crews repo bypassed the dispatcher entirely, partly because it was the wrong abstraction for the job.

## Decision

**No crew defines a dispatcher. The dispatcher is always auto-generated at the project level.**

The generator synthesizes a dispatcher from the project's crew composition:
1. Collects all `type: orchestrator` agents across deployed crews → these are leads
2. Collects all `shared: true` agents → these are cross-crew utilities
3. Builds a routing table from each lead's `routes:` field
4. Generates a prompt with: self-execute heuristic, planning/sequencing instructions, routing table
5. Writes to `.kiro/agents/dispatcher.json` with `ctrl+shift+d` shortcut

The dispatcher gets `read`, `shell`, `write`, `subagent`, `todo_list`:
- Self-executes atomic tasks (≤1 tool call, no prior reading needed)
- Routes to shared utilities for one-shot specialist tasks
- Delegates to crew leads for all multi-step work
- Plans task graphs for complex requests before dispatching

### Customization

Projects can override via `.crews/crew.yaml`:
```yaml
dispatcher:
  include_meta: false      # include meta crew agents (default: false)
  include_kiro_helper: true  # include kiro-helper utility (default: false)
  prompt_suffix: |         # appended to generated prompt
    ## Project Rules
    Always run tests before marking done.
```

### Meta Crew Alignment

The meta crew removes its `type: dispatcher` archetype and follows the same pattern as all other crews: leads + workers. The auto-generated dispatcher for the agent-crews project routes to build-lead, ops-lead, bugfix-lead — derived from the meta crew's orchestrator archetypes.

## Alternatives Considered

- **Keep dispatcher in meta.yaml, fix its prompt per-project.** Rejected — the dispatcher's routing table is entirely project-specific. A static definition can't adapt.
- **Define dispatcher in general.yaml (always included).** Rejected — the dispatcher's content depends on ALL crews, not just general. It must be synthesized after all crews are known.
- **Let users define their own dispatcher.** Rejected as default — too much boilerplate. Auto-generation with optional overrides gives the best of both.

## Consequences

- Every project gets a correct dispatcher automatically — no manual wiring
- Adding/removing crews automatically updates the dispatcher's routing
- The meta crew follows the same pattern as all other crews (no special case)
- Projects that previously had the meta dispatcher will get a project-appropriate one on next build
- The `type: dispatcher` archetype in YAML becomes unused (only the generator creates dispatchers)
