# Proposal: Meta Crew Rework

## Status: Draft
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

## Proposed Architecture

```
Dispatcher (depth 0) — routes OR executes simple tasks directly
├── build-lead (depth 1, orchestrator)
│   ├── crew-researcher (research before building)
│   ├── crew-creator (new projects)
│   └── crew-augmenter (modify existing)
├── ops-lead (depth 1, orchestrator)
│   ├── crew-analyst (observe)
│   ├── crew-doctor (diagnose/fix crew issues)
│   ├── crew-validator (verify)
│   └── project-hygiene (maintain)
├── bugfix-lead (depth 1, orchestrator)
│   ├── meta-debugger (root-cause analysis on scripts/generation)
│   └── meta-tester (eval writing, smoke tests)
├── kiro-helper (direct utility — CLI/tooling issues)
└── crew-releaser (direct utility — release is a single workflow)
```

### Key Design Decisions

**Dispatcher gets execution tools.** For "run just build", "write this file", "git status" — the dispatcher handles it directly. No routing overhead for atomic tasks. This addresses the 46% of sessions that are direct commands.

**Bug-fix crew added.** 14% bugs + 11% testing = 25% of intent. The meta crew currently has no systematic debugging capability for its own tooling (generate.py, scripts, session-ingest.py). `crew-doctor` handles broken agent configs, but not broken Python scripts or shell failures.

**Releaser stays direct (not under ops-lead).** Just added — keep as a direct dispatcher target until session data (via `session-diff --since-change`) shows it needs coordination with other ops agents.

**3 crews, not 2.** Original proposal was build + ops. Adding bug-fix because the session data shows clear signal (25% intent) and the work is distinct from ops (fixing code vs. validating configs).

## Change-Point Markers

### Problem

`session-diff.sh` compares sessions before/after a date. But:
- You have to remember WHEN you changed agents
- Multiple changes on the same day are indistinguishable
- No way to correlate "performance improved" with "which specific change caused it"

### Solution: `.crew-changelog` markers

After `just build`, record a change-point marker:

```yaml
# scratch/change-markers.yaml (gitignored, local analysis data)
markers:
  - date: "2025-05-15T14:44:01"
    commit: "b661f19"
    description: "3-level hierarchy with dispatcher type"
    agents_changed: [dispatcher, general-lead, all-workers]
    project: agent-crews
    
  - date: "2025-05-15T14:28:27"  
    commit: "0c8b80f"
    description: "crew-releaser agent added"
    agents_changed: [crew-releaser, dispatcher]
    project: agent-crews
```

**Implementation:**
1. `just build` appends a marker with git commit SHA + changed files
2. `session-diff.sh` accepts `--since-change <commit>` instead of raw dates
3. `crew-health.sh` reports "days since last change" and "sessions since last change" per agent

## Enhanced Analysis Capabilities

### New analyses (from this session's manual work)

| Analysis | Current | Proposed |
|----------|---------|----------|
| Agent distribution | Manual python one-liner | `analyze-session.py --agent-distribution <project>` |
| Crew bypass detection | Manual categorization | `analyze-session.py --bypass-report <project>` |
| Workflow clustering | Manual timestamp analysis | `analyze-session.py --clusters <project>` |
| Intent vs. routing match | Not automated | `crew-health.sh` reports "intent X has no matching crew" |

### `--bypass-report` output

```
=== Crew Bypass Report: agent-crews ===

Sessions using crew agents: 4/136 (3%)
Sessions bypassing crew: 90/136 (66%)

Work that should route to:
  build-lead        44 sessions (creator + augmenter + researcher work)
  ops-lead          20 sessions (analyst + validator + doctor work)
  bugfix-lead       16 sessions (fix + debug + test work)
  crew-releaser      8 sessions (release + changelog work)
  
Direct execution (appropriate bypass): 23 sessions
Uncategorized: 20 sessions

Recommendation: Reduce routing friction. Dispatcher should handle
atomic tasks directly. Consider keyboard shortcuts for leads.
```

### `--clusters` output

```
=== Workflow Clusters: agent-crews (last 7 days) ===

Cluster 1 (7 sessions, 45min span):
  Intent: crew-creation + docs + release
  Agents: dispatcher(2), default(4), kiro_default(1)
  Pattern: Multi-tool workflow, mostly bypassing crew

Cluster 2 (16 sessions, 3.2h span):
  Intent: phased-implementation (release tooling)
  Agents: default(16)
  Pattern: Sequential implementation, zero crew usage
  Recommendation: This is build-lead territory
```

## Bug-Fix Crew Definition

```yaml
workflow: meta-bugfix

scope:
  description: "Fix broken scripts, generation failures, and tooling issues in agent-crews"
  handles:
    - bugs
    - testing
    - debugging
  refuses:
    - features
    - research
    - documentation

agents:
  - type: orchestrator
    agents:
      - name: bugfix-lead
        description: "[Meta] Bug-fix orchestrator — systematic debugging of agent-crews tooling"
        routes: "Something is broken in generate.py, scripts, or session tooling"
        prompt: |
          You are bugfix-lead for the agent-crews repo itself.
          Coordinate debugging of: generate.py, session-ingest.py, scripts/*, justfile recipes.
          
          ## Workflow
          1. Reproduce → meta-debugger
          2. Root-cause → meta-debugger  
          3. Fix → meta-debugger (or delegate to build-lead if it's a feature gap)
          4. Verify → meta-tester
          5. Regression test → meta-tester

  - type: worker
    agents:
      - name: meta-debugger
        description: "[Meta] Debugger — root-cause analysis on agent-crews tooling"
        routes: "Need to find why a script/generator/recipe is failing"
        prompt: |
          You are meta-debugger — fix broken tooling in agent-crews.
          Targets: generate.py, session-ingest.py, scripts/*, justfile, hooks.
          
          ## Protocol
          1. Reproduce the failure (exact command + error)
          2. Five Whys to root cause
          3. Minimal fix (don't refactor while fixing)
          4. Verify fix resolves original error
          
          ## Common failure modes
          - generate.py: YAML parse errors, missing keys, template failures
          - session-ingest.py: missing session dirs, tool format changes
          - scripts: path assumptions, missing dependencies, permission issues
          - justfile: recipe ordering, variable expansion, missing tools

      - name: meta-tester
        description: "[Meta] Tester — evals, smoke tests, regression checks"
        routes: "Need tests written or run for agent-crews tooling"
        prompt: |
          You are meta-tester — ensure agent-crews tooling works correctly.
          
          ## What you test
          - `just build` succeeds for all projects
          - `just check` passes
          - Smoke tests: `just smoke-test <path>`
          - Eval runs: `just eval <project>`
          - Regression: verify fixed bugs stay fixed
          
          ## After any fix
          Run the full verification suite, not just the specific failing case.
```

## Migration Plan

1. **Phase 1: Change markers** — Add marker generation to `just build`. Low risk, immediate value.
2. **Phase 2: Enhanced analysis** — Add `--bypass-report`, `--clusters`, `--agent-distribution` to analyze-session.py.
3. **Phase 3: Bug-fix crew** — Add meta-bugfix crew definition, wire into dispatcher.
4. **Phase 4: 3-level restructure** — Split current flat agents into build-lead + ops-lead hierarchy.
5. **Phase 5: Dispatcher execution** — Give dispatcher shell/write tools for atomic tasks.

Each phase is independently deployable. Phase 1-2 inform whether Phase 3-5 are working.

## What NOT to change yet

- **crew-releaser** — recently added. Use `session-diff --since-change` to evaluate before restructuring.
- **Theme system** — unrelated to this rework.
- **Component architecture** — works fine, no session signal suggesting issues.
- **Deployed crews (general, bug-fix, etc.)** — this proposal is meta-crew only.

## Success Criteria

After implementation, measure:
- Crew bypass rate drops from 68% to <30%
- Dispatcher sessions show <5 file re-reads per file
- Bug-fix intent routes to bugfix-lead (not default agent)
- Change markers enable `session-diff --since-change` workflow
- Avg session duration drops (better task decomposition via leads)
