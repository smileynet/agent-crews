# Proposal: Meta Crew Rework

## Status: Approved
## Date: 2025-05-15

## Problem Statement

The meta crew (agents for working on this repo) has three issues:

1. **Flat architecture** — dispatcher routes directly to 9 workers, violating the 3-level hierarchy this repo deploys to other projects
2. **68% crew bypass** — users work with the `default` agent for tasks the crew should handle
3. **No bug-fix capability** — 14% of session intent is bugs/testing with no dedicated crew
4. **No change-point tracking** — session-diff compares before/after a date, but doesn't know WHAT changed or WHEN agents were modified

## Session Evidence

| Signal | Value | Implication |
|--------|-------|-------------|
| Sessions using default agent | 132/136 (97%) | Crew isn't being used |
| Work that SHOULD route through crew | 90/133 (68%) | Routing friction too high |
| Intent: features | 39% | Build crew needed |
| Intent: bugs/testing | 25% combined | Bug-fix crew needed |
| Intent: mixed-work | 25% | Direct-execution path needed |
| Avg session duration | 2.4h | Multi-step work, needs planning layer |
| Files re-read across subagents | 11-23x per session | Shared context missing |
| Dispatcher subagent calls | 35-78 per session | Too much delegation overhead |

## Architecture

```
Dispatcher (depth 0) — routes OR executes simple tasks directly
│   Tools: read, shell, write, subagent, todo_list
│   Shortcut: ctrl+shift+d
│
├── build-lead (depth 1, orchestrator)
│   Tools: read, subagent, todo_list
│   ├── crew-researcher (research before building)
│   ├── crew-creator (new projects)
│   └── crew-augmenter (modify existing)
│
├── ops-lead (depth 1, orchestrator)
│   Tools: read, subagent, todo_list
│   ├── crew-analyst (observe)
│   ├── crew-doctor (diagnose/fix crew configs)
│   ├── crew-validator (verify)
│   └── project-hygiene (maintain)
│
├── bugfix-lead (depth 1, orchestrator)
│   Tools: read, subagent, todo_list
│   ├── meta-debugger (root-cause analysis on scripts/generation)
│   └── meta-tester (eval writing, smoke tests)
│
├── kiro-helper (direct utility — CLI/tooling issues)
└── crew-releaser (direct utility — release workflow)

Utilities (crew-agnostic, dispatched by any lead):
├── verifier
└── editor
```

## Dispatcher Routing

The dispatcher checks in this order:

| Priority | Pattern | Target |
|----------|---------|--------|
| 1 | Simple command (≤1 tool call, no reading needed) | Execute directly |
| 2 | Create/modify/research crews | build-lead |
| 3 | Analyze, diagnose, validate, maintain | ops-lead |
| 4 | Fix broken scripts/generation/tooling | bugfix-lead |
| 5 | Release, version bump, publish | crew-releaser |
| 6 | Kiro CLI issues, MCP config | kiro-helper |

"Execute directly" heuristic: if the request can be completed in ≤1 tool call with no prior file reading, the dispatcher handles it itself (e.g., "run just build", "git status", "write this file").

## Key Design Decisions

**Dispatcher gets execution tools.** `read`, `shell`, `write`, `subagent`, `todo_list`. Addresses 46% of sessions that are direct commands. Bounded by the ≤1 tool call heuristic.

**Leads get `read` + `subagent` + `todo_list` only.** They gather context and delegate. No `shell` or `write` — that's worker territory.

**Bug-fix crew has two workers.** `meta-debugger` (root-cause + fix) and `meta-tester` (independent verification). Enforces "don't mark your own homework."

**`crew-doctor` under ops-lead, `meta-debugger` under bugfix-lead.** Different failure domains: crew-doctor fixes agent configs/behavior (YAML), meta-debugger fixes broken code (Python/shell). Dispatcher disambiguates if unclear.

**`crew-researcher` exclusively under build-lead.** Research is 1% of intent — not worth shared-worker complexity. Ops-lead routes research needs through dispatcher if needed.

**`crew-releaser` stays direct.** Recently added. Use `session-diff --since-change` to evaluate before restructuring.

**Only dispatcher gets a keyboard shortcut.** All other shortcuts removed (crew-creator's `ctrl+shift+c`, crew-doctor's `ctrl+shift+f`). Leads accessed via dispatcher routing or `/agent <name>`.

**Workers lose subagent access.** crew-creator and crew-doctor currently dispatch to kiro-helper — replaced with kiro-cli-schema skill as a resource. Respects "workers can't delegate" guardrail.

**`verifier` and `editor` unchanged.** Already crew-agnostic utilities, dispatched by any lead.

## Generator Change Required

One fix needed before Phase 4:

```python
# Current (overwrites explicit config):
ts.setdefault("subagent", {})["availableAgents"] = crew_workers
ts["subagent"]["trustedAgents"] = crew_workers

# Fix (respects explicit config):
sub = ts.setdefault("subagent", {})
if "availableAgents" not in sub:
    sub["availableAgents"] = crew_workers
    sub["trustedAgents"] = crew_workers
```

This allows leads to declare explicit `availableAgents` in YAML without the generator overwriting them. Backwards-compatible — crews without explicit scoping still get auto-scoped.

## Change-Point Markers

### Problem

`session-diff.sh` compares sessions before/after a date, but doesn't know what changed or when.

### Solution

Post-build script `scripts/mark-change.sh`:
1. After `uv run generate.py`, check `git diff --name-only` on the output directory
2. If files changed, append marker to `scratch/change-markers.yaml`
3. If no files changed, do nothing

```yaml
# scratch/change-markers.yaml (gitignored)
markers:
  - date: "2025-05-15T14:44:01"
    commit: "b661f19"
    description: "3-level hierarchy with dispatcher type"
    agents_changed: [dispatcher, general-lead, all-workers]
    project: agent-crews
```

`session-diff.sh` gains `--since-change <commit>` flag to use markers instead of raw dates.

## Enhanced Analysis

New modes added to `analyze-session.py`:

| Flag | Purpose |
|------|---------|
| `--agent-distribution <project>` | Show which agents handle sessions |
| `--bypass-report <project>` | Detect work that should route through crew |
| `--clusters <project>` | Group sessions into workflow clusters by timestamp |

### Bypass Detection (combines two signals)

1. **Intent classification** (from session-ingest) → maps intent to expected crew
2. **Routing table pattern match** — parse dispatcher's patterns from meta.yaml, match against session titles

| Both agree | Meaning |
|------------|---------|
| Intent + routing agree → used default | High confidence bypass |
| Intent matches crew, routing has no pattern | Routing gap (dispatcher needs new route) |
| Routing matches, intent doesn't | Intent classifier needs updating |
| Signals disagree | Ambiguous — show both, flag for review |

## Bug-Fix Crew Definition

```yaml
- type: orchestrator
  tools: [read, subagent, todo_list]
  allowedTools: [read, subagent, todo_list]
  agents:
    - name: bugfix-lead
      description: "[Meta] Bug-fix orchestrator — systematic debugging of agent-crews tooling"
      routes: "Something is broken in generate.py, scripts, or session tooling"
      toolsSettings:
        subagent:
          availableAgents: [meta-debugger, meta-tester]
          trustedAgents: [meta-debugger, meta-tester]

- type: worker
  agents:
    - name: meta-debugger
      description: "[Meta] Debugger — root-cause analysis on agent-crews tooling"
      routes: "Need to find why a script/generator/recipe is failing"
      # Targets: generate.py, session-ingest.py, scripts/*, justfile, hooks

    - name: meta-tester
      description: "[Meta] Tester — evals, smoke tests, regression checks"
      routes: "Need tests written or run for agent-crews tooling"
      # Runs: just build, just check, just smoke-test, just eval
```

## Migration Plan

| Phase | What | Risk | Commit strategy |
|-------|------|------|-----------------|
| 1 | Change markers (`scripts/mark-change.sh` + justfile integration) | Low | Single commit |
| 2 | Enhanced analysis (`--bypass-report`, `--clusters`, `--agent-distribution`) | Low | Single commit |
| 3 | Bug-fix crew (add bugfix-lead + meta-debugger + meta-tester to meta.yaml) | Low | Single commit |
| 5 | Dispatcher execution (add `shell` + `write` to dispatcher, add self-execute heuristic) | Low | Single commit |
| 4 | 3-level restructure | Medium | Two commits: (a) generator fix, (b) full YAML restructure |

Order rationale: measurement infrastructure first (1-2), then additive changes (3, 5), then the big restructure last (4) — validated by the analysis tools from Phase 2.

## What NOT to Change

- **crew-releaser** — recently added. Use `session-diff --since-change` to evaluate before restructuring.
- **Theme system** — unrelated to this rework.
- **Component architecture** — no session signal suggesting issues.
- **Deployed crews (general, bug-fix, etc.)** — this proposal is meta-crew only.
- **Single meta.yaml file** — keep until it exceeds ~700 lines.

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Crew bypass rate | 68% | <30% |
| File re-reads per session | 11-23x | <5x |
| Bug-fix intent routing | 0% to crew | >80% to bugfix-lead |
| Change marker coverage | none | every build-with-diff gets a marker |
| Avg session duration | 2.4h | decrease (better task decomposition) |
