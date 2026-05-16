# Implementation Spec: Build-Time Context Injection

**Status:** Draft v2  
**Date:** 2026-05-16  
**Depends on:** ADR-010 (eval harness), ADR-001 (enforcement over suggestion)  
**Supersedes:** Component Architecture Spec Section 3.3 (resource globs — never implemented)

## Drift Analysis

The Component Architecture Spec (2026-05-11) designed per-archetype resource globs:
```json
// Orchestrator (spec Section 3.3)
"resources": ["file://.kiro/steering/universal/*.md", "file://.kiro/steering/orchestrator/*.md"]
// Worker (spec Section 3.3)  
"resources": ["file://.kiro/steering/universal/*.md", "file://.kiro/steering/worker/*.md"]
```

**This was never implemented.** The generator writes steering files to the correct directories (Step 6 of spec Section 6.2) but never adds resource globs to agent JSON (Step 7 incomplete). Result: 23 steering files exist but are invisible to all custom agents.

**Why it wasn't caught:** The `kiro_default` agent (no `--agent` flag) loads `.kiro/steering/**/*.md` via its built-in behavior. Manual testing without specifying an agent shows correct behavior. Custom agents bypass this entirely.

**Revised approach:** Rather than implementing the spec's always-on globs (which would add ~8K tokens to every agent), we use the spec's own skill mechanism for on-demand delivery. This honors both the original intent (archetype-targeted) and context budget research (precision over volume).

## Platform Assumptions

These assumptions about kiro-cli behavior underpin all design decisions. Each has a validation test (see Assumption Tests section).

| ID | Assumption | Source | Validated |
|----|-----------|--------|:---------:|
| A1 | Custom agents do NOT inherit `.kiro/steering/**/*.md` | kiro-cli docs: "Built-in Default Agent" section | Pending |
| A2 | Custom agents only get context from explicit `resources` field | kiro-cli docs: "Agent Configuration" | Pending |
| A3 | `skill://` resources load metadata at startup, full content on demand | kiro-cli docs: "Skills progressively loaded on demand" | Pending |
| A4 | `file://` resources are always loaded into context | kiro-cli docs: "Files always loaded into context" | Pending |
| A5 | Subagents spawned via `subagent` tool get their OWN agent config, not parent's | Component spec Section 11.2 | Pending |
| A6 | `file://` supports glob patterns (e.g., `file://src/**/*.rs`) | kiro-cli docs: "Both support glob patterns" | Pending |
| A7 | Resources cascade: workflow → archetype → agent (agent extends, not replaces) | generate.py `build_agent()` line 59 (our code) | Confirmed |

## Problem

Our agents operate with minimal context. Custom agents only receive what's explicitly in their `resources` field. Currently:

- `file://AGENTS.md` (all agents) — always loaded
- `file://.kiro/steering/vocabulary.md` (most agents) — always loaded
- Agent-specific skills (some agents) — on-demand

The 23 steering files (verification, git, troubleshooting, completion, etc.) are **invisible** to custom agents. Protocols must be delivered as skills (on-demand) or injected into prompts.

## Design Principles

1. **Precision over volume** — a focused 300-token context outperforms an unfocused 113K context
2. **Inject at build time what's known at build time** — routing tables, worker lists, project commands
3. **Use skills for situational protocols** — verification, git, troubleshooting (loaded when relevant)
4. **Use file:// resources sparingly** — only for content needed every single turn
5. **Enforce via tools, guide via prompt, reference via skills** — the enforcement hierarchy

## Architecture

```
Source YAML (base/crews/*.yaml)
    ↓ generate.py
Agent JSON (.kiro/agents/*.json)
    ├── prompt: (injected routing tables, worker context, scope)
    ├── resources:
    │   ├── file:// (always-loaded: AGENTS.md, vocabulary)
    │   └── skill:// (on-demand: protocols, reference material)
    └── tools: (enforced capabilities)
```

### Context Budget Per Archetype

| Archetype | Prompt (injected) | file:// (always) | skill:// (on-demand) |
|-----------|-------------------|------------------|---------------------|
| Dispatcher | Routing table, scope boundary | AGENTS.md | — |
| Orchestrator | Worker table, routing table, scope, handoff | vocabulary.md | completion-protocol |
| Worker | Scope & siblings, project commands | AGENTS.md, vocabulary.md | verification, git, troubleshooting |
| Verifier/Editor | Minimal (fresh judgment) | — | — |

## Implementation

### Phase 0: Assumption Validation Tests (GATE)

Before implementing anything, validate platform assumptions with repeatable tests. All must pass before proceeding.

### Phase 1: Protocol Skills

Convert steering docs into skills with proper frontmatter for on-demand loading.

**Worker skills:**
- `shared/skills/verification-protocol/SKILL.md` ← from steering/worker/verification.md
- `shared/skills/git-protocol/SKILL.md` ← from steering/worker/git.md
- `shared/skills/troubleshooting-protocol/SKILL.md` ← from steering/worker/troubleshooting.md

**Orchestrator skills:**
- `shared/skills/completion-protocol/SKILL.md` ← from steering/universal/completion.md

**Generator change:** Add skills to agent resources based on archetype.

### Phase 2: Build-Time Injection (leads)

- `inject_worker_context()` — auto-inject worker table into orchestrator prompts
- Remove `read` from all orchestrator tool lists
- Remove hand-written worker sections from lead prompts

### Phase 3: Build-Time Injection (workers)

- `inject_scope_and_siblings()` — auto-inject scope + sibling list for refusal/redirect
- `inject_project_commands()` — from verification config

### Phase 4: Eval Context Measurement

- `--measure-context` flag on eval harness
- Token budget tracking in meta.json
- Warning threshold at 8K static tokens

### Phase 5: Dispatcher Scope Boundary

- Inject refuses list into dispatcher prompt

---

## Assumption Tests

Repeatable tests that validate platform behavior. Run before implementation and after kiro-cli updates.

### Structure

```
tests/assumptions/
├── run.sh                         # Orchestrates all tests, reports pass/fail
├── fixtures/
│   ├── agents/
│   │   ├── bare-agent.json        # No resources at all
│   │   ├── file-resource-agent.json   # Has file:// resource
│   │   ├── skill-resource-agent.json  # Has skill:// resource
│   │   ├── glob-resource-agent.json   # Has glob pattern resource
│   │   ├── parent-agent.json      # Has subagent tool + own canary
│   │   └── child-agent.json       # Subagent target with own canary
│   ├── canary-file.md             # Contains "CANARY_FILE_7X9Q2"
│   ├── parent-canary.md           # Contains "PARENT_ONLY_3Z7W5"
│   ├── child-canary.md            # Contains "CHILD_ONLY_9R2X8"
│   ├── glob-test/
│   │   ├── a.md                   # Contains "GLOB_A_5T3K"
│   │   └── b.md                   # Contains "GLOB_B_8M2N"
│   └── test-skill/
│       └── SKILL.md               # Frontmatter + "SKILL_CONTENT_4K8M1"
└── results/
    └── <timestamp>.json           # Test results with kiro-cli version
```

### Test Definitions

#### T1: Custom agents don't auto-load steering (A1)

```bash
# bare-agent.json: tools: [read], resources: [], prompt: "You are a test agent."
# .kiro/steering/worker/verification.md exists with known content
INPUT="Do you have access to any verification protocol or steering files? Quote any you can see."
PASS_IF="Agent cannot quote steering content"
FAIL_IF="Agent quotes verification protocol text"
```

#### T2: file:// resources are always loaded (A4)

```bash
# file-resource-agent.json: resources: ["file://tests/assumptions/fixtures/canary-file.md"]
INPUT="What is the canary phrase in your context?"
PASS_IF="Agent responds with CANARY_FILE_7X9Q2"
FAIL_IF="Agent doesn't know the phrase"
```

#### T3: skill:// loads on demand, not always (A3)

```bash
# skill-resource-agent.json: resources: ["skill://tests/assumptions/fixtures/test-skill/SKILL.md"]
# test-skill/SKILL.md frontmatter: description: "Use when asked about flamingos"
# Content: "SKILL_CONTENT_4K8M1"

# 3a: Unrelated question — skill should NOT load
INPUT="What is 2+2?"
PASS_IF="Response does NOT contain SKILL_CONTENT_4K8M1"

# 3b: Trigger question — skill SHOULD load  
INPUT="Tell me about flamingos"
PASS_IF="Response references skill content"
```

#### T4: Subagents get own config, not parent's (A5)

```bash
# parent-agent.json: resources: ["file://tests/assumptions/fixtures/parent-canary.md"], 
#   tools: [read, subagent], toolsSettings.crew.availableAgents: [child-agent]
# child-agent.json: resources: ["file://tests/assumptions/fixtures/child-canary.md"]
INPUT="Delegate to child-agent: ask what canary phrases are in your context"
PASS_IF="Child reports CHILD_ONLY_9R2X8 but NOT PARENT_ONLY_3Z7W5"
FAIL_IF="Child sees parent's canary phrase"
```

#### T5: file:// glob patterns work (A6)

```bash
# glob-resource-agent.json: resources: ["file://tests/assumptions/fixtures/glob-test/*.md"]
INPUT="What phrases do you see from glob-test files?"
PASS_IF="Agent reports both GLOB_A_5T3K and GLOB_B_8M2N"
FAIL_IF="Either phrase missing"
```

#### T6: No auto-loading without explicit resource (A2)

```bash
# bare-agent.json: resources: [] (empty)
# AGENTS.md exists in project root
INPUT="Quote the first line of AGENTS.md from your context"
PASS_IF="Agent says it doesn't have AGENTS.md in context"
FAIL_IF="Agent quotes AGENTS.md content without reading it via tool"
```

### Test Runner Design

```bash
#!/bin/bash
# tests/assumptions/run.sh
set -euo pipefail

KIRO_VERSION=$(kiro-cli --version)
TIMESTAMP=$(date -u +%Y-%m-%dT%H-%M-%SZ)
RESULTS="tests/assumptions/results/${TIMESTAMP}.json"
PASS=0; FAIL=0; ERRORS=()

run_test() {
    local name="$1" agent="$2" input="$3" pass_pattern="$4" fail_pattern="$5"
    output=$(kiro-cli chat --no-interactive -a --agent "$agent" "$input" 2>&1 | head -100)
    
    if echo "$output" | grep -qi "$fail_pattern"; then
        ERRORS+=("FAIL: $name — matched fail pattern")
        ((FAIL++))
    elif echo "$output" | grep -qi "$pass_pattern"; then
        ((PASS++))
    else
        ERRORS+=("INCONCLUSIVE: $name — matched neither pattern")
        ((FAIL++))
    fi
}

# ... test invocations ...

echo "{\"kiro_version\": \"$KIRO_VERSION\", \"timestamp\": \"$TIMESTAMP\", \"passed\": $PASS, \"failed\": $FAIL, \"errors\": [$(printf '"%s",' "${ERRORS[@]}")]}" > "$RESULTS"
```

### When to Run

- **Before implementing any phase** (gate)
- **After kiro-cli updates** (regression detection)
- **When agent behavior is unexpected** (first diagnostic: did assumptions change?)
- **In CI** (if kiro-cli is available in CI environment)

---

## Validation Criteria

1. All assumption tests pass (Phase 0 gate)
2. `just build` produces valid JSON for all agents
3. No agent exceeds 8K tokens of static context
4. Routing evals pass at same or better rate
5. Execution evals improve (workers have verification protocol)
6. Skills load on-demand (verify with `/context show`)

## Risks

| Risk | Mitigation |
|------|------------|
| Skills not triggering when needed | Precise descriptions + T3 validates mechanism |
| kiro-cli changes resource loading | Assumption tests catch immediately |
| Injected tables too long | Token monitoring; tables are ~50 tokens/worker |
| Protocol skills conflict with prompt | Skills supplement — prompt is authoritative |
| Assumption A3 is wrong (skills always load) | T3 validates; if wrong, use file:// with minimal content |

## Sequence

```
Phase 0 (assumptions) → GATE for all other phases
Phase 1 (skills)      → immediate value, no breaking changes  
Phase 2 (leads)       → depends on Phase 1
Phase 3 (workers)     → independent of Phase 2
Phase 4 (eval)        → after Phases 1-3 stabilize
Phase 5 (dispatcher)  → trivial, do alongside Phase 2
```
