# Proposal: Auto-Generated Dispatcher & Cross-Crew Utilities

## Status: Approved
## Date: 2025-05-15

## Problem Statement

After the meta crew rework, three architectural issues remain:

1. **Deployed projects get the wrong dispatcher** — the meta crew's dispatcher (talks about agent-crews repo, routes to crew-creator/crew-doctor) is deployed verbatim to target projects instead of routing to their actual crew leads
2. **Cross-crew utility agents aren't accessible** — verifier (bug-fix crew) and editor (research crew) can't be dispatched by other crews' leads, breaking the completion and writing protocols
3. **Meta crew is a special case** — it's the only crew that defines a `type: dispatcher`, violating the consistent pattern all other crews follow

## Architecture (After)

```
Auto-generated dispatcher (project-level, not crew-defined)
│   Tools: read, shell, write, subagent, todo_list
│   Routes to: all leads + shared utilities
│   Self-executes: atomic tasks (≤1 tool call)
│   Plans: task graphs for multi-step work
│
├── general-lead (from general crew)
├── bugfix-lead (from bug-fix crew)
├── research-lead (from research crew)
├── [other leads from deployed crews...]
│
└── Shared utilities (accessible to all orchestrators):
    ├── verifier (home: bug-fix crew, shared: true)
    ├── editor (home: research crew, shared: true)
    └── kiro-helper (home: meta crew, shared: true)
```

Every crew follows the same pattern: **leads + workers**. No crew defines a dispatcher.

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Dispatcher routes to project leads, not meta agents | Current behavior deploys wrong dispatcher |
| 2 | Dispatcher auto-generated with read/shell/write/subagent/todo_list + self-execute + planning instructions | Derived from crew composition |
| 3 | Project leads only by default; optional include_meta/include_kiro_helper | Centralized crew management is best practice |
| 4 | Shared agents injected into ALL orchestrators | One-shot utilities don't need a lead in the middle |
| 5 | Strong planning/sequencing instructions in dispatcher | Ensures crews used effectively |
| 6 | Welcome message shows crews + prompt references | Discoverability |
| 7 | Customization via `dispatcher:` section in crew.yaml | Co-located, absent = auto-generated |
| 8 | AGENTS.md: marker-based insertion, point to crew-sheet | Idempotent, respects project content |
| 9 | Defer meta.yaml size reduction; backlog → GitHub issues | Low priority |
| 10 | Skip component subagent if crew agent exists (no merge) | Crew version is richer |
| 11 | ctrl+shift+d default shortcut | Established convention |
| 12 | No crew defines a dispatcher — always auto-generated | Eliminates special case |
| 13 | crew-releaser under ops-lead; kiro-helper shared | Clean hierarchy |
| 14 | Dispatcher routes to leads + shared utilities; strong delegation instructions | Prevents absorbing work |
| 15 | Generator uses type: orchestrator as leads, shared: true as utilities | Existing structure provides signal |
| 16 | Dispatcher written to .kiro/agents/dispatcher.json | Consistent with all agents |
| 17 | ops-lead gets crew-releaser; kiro-helper gets shared: true | Implements decisions 12-13 |

## References

- [ADR-008: Auto-Generated Project Dispatcher](../decisions/ADR-008-auto-generated-dispatcher.md)
- [ADR-009: Shared Utility Agents](../decisions/ADR-009-shared-utility-agents.md)
- [Implementation Spec](../specs/auto-dispatcher-and-shared-utilities.md)

## Implementation Order

1. **Shared utilities** — `shared: true` flag, collection, injection, deduplication
2. **Auto-generated dispatcher** — synthesis function, prompt template, remove from meta.yaml
3. **AGENTS.md management** — marker-based insertion

## Success Criteria

| Metric | How to verify |
|--------|--------------|
| All leads can dispatch verifier/editor | Check `availableAgents` in generated JSON |
| Dispatcher routes to project leads | Check examples after regeneration |
| No `type: dispatcher` in any crew YAML | `grep -r 'type: dispatcher' base/crews/` returns nothing |
| Meta crew follows same pattern as others | Only has orchestrator + worker types |
| AGENTS.md stays accurate | Marker content matches crew-sheet |
| Existing evals pass | `just eval agent-crews` |
