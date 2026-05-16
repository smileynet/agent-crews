# Implementation Spec: Build-Time Context Injection

**Status:** Draft  
**Date:** 2026-05-16  
**Depends on:** ADR-010 (eval harness), ADR-001 (enforcement over suggestion)

## Problem

Our agents operate with minimal context. Custom agents in kiro-cli only receive what's explicitly in their `resources` field — they do NOT inherit `.kiro/steering/**/*.md` (that's a `kiro_default`-only behavior). Currently our agents get:

- `file://AGENTS.md` (all agents)
- `file://.kiro/steering/vocabulary.md` (most agents)
- Agent-specific skills (some agents)

This means:
- Verification protocol, git protocol, troubleshooting protocol — **not loaded**
- Completion protocol, signaling protocol — **not loaded**
- The 23 steering files we wrote are **invisible** to custom agents

Meanwhile, agents that need routing context (leads) have it hand-written in prompts, which drifts from source YAML.

## Design Principles

1. **Precision over volume** — a focused 300-token context outperforms an unfocused 113K context (MECW research)
2. **Inject at build time what's known at build time** — routing tables, worker lists, project commands
3. **Use skills for on-demand context** — protocols that apply situationally (not every turn)
4. **Use resources for always-needed context** — AGENTS.md, vocabulary
5. **Enforce via tools, guide via prompt, reference via skills** — the enforcement hierarchy

## Architecture

```
Source YAML (base/crews/*.yaml)
    ↓ generate.py
Agent JSON (.kiro/agents/*.json)
    ├── prompt: (injected routing tables, worker context, scope)
    ├── resources: (always-loaded files — AGENTS.md, vocabulary)
    └── skills: (on-demand protocols — verification, git, troubleshooting)
```

### Context Budget Per Archetype

| Archetype | Prompt (injected) | Resources (always) | Skills (on-demand) |
|-----------|-------------------|--------------------|--------------------|
| Dispatcher | Routing table, scope boundary | AGENTS.md | — |
| Orchestrator | Worker table, routing table, scope, handoff | vocabulary.md | — |
| Worker | Scope & siblings, project commands | AGENTS.md, vocabulary.md | verification, git, troubleshooting (archetype-specific) |

### Why Skills for Protocols

Skills are loaded **on demand** by kiro-cli — their metadata (name, description) is always present but full content only loads when relevant. This is perfect for protocols:
- Verification protocol: loaded when agent is about to report DONE
- Git protocol: loaded when agent is about to commit
- Troubleshooting protocol: loaded when agent encounters an error

This keeps the active context small while making protocols available when needed.

## Implementation

### Phase 1: Targeted Protocol Skills (highest value)

Convert archetype-specific steering docs into skills that agents can reference on demand.

**Worker skills (add to all worker agents):**
```yaml
resources:
  - skill://shared/skills/verification-protocol/SKILL.md
  - skill://shared/skills/git-protocol/SKILL.md
  - skill://shared/skills/troubleshooting-protocol/SKILL.md
```

**Create from existing steering:**
- `shared/skills/verification-protocol/SKILL.md` ← from `.kiro/steering/worker/verification.md`
- `shared/skills/git-protocol/SKILL.md` ← from `.kiro/steering/worker/git.md`
- `shared/skills/troubleshooting-protocol/SKILL.md` ← from `.kiro/steering/worker/troubleshooting.md`

Each gets YAML frontmatter with name + description (triggers on-demand loading):
```yaml
---
name: verification-protocol
description: Gate workflow for verifying work before reporting DONE. Use before marking any task complete.
---
```

**Orchestrator skills (add to all orchestrator agents):**
```yaml
resources:
  - skill://shared/skills/completion-protocol/SKILL.md
```

- `shared/skills/completion-protocol/SKILL.md` ← from `.kiro/steering/universal/completion.md`

**NOT converted to skills (stay as prompt injection):**
- Routing tables — needed every turn, not situational
- Worker lists — needed every turn for routing decisions
- Scope boundaries — needed every turn to refuse wrong work

### Phase 2: Build-Time Injection (leads)

**`inject_worker_context()`** — add to `generate.py`:

For each orchestrator agent, after building the agent JSON, inject:
```markdown

## Your Workers

| Worker | Handles | Key Tools |
|--------|---------|-----------|
| {name} | {routes} | {tools - [read]} |

Delegate the FULL task. Workers have tools you don't.
```

Source: same-crew worker agents' `name`, `routes`, and `tools` fields.

**Remove `read` from orchestrator tool lists** in all base crews.

**Remove hand-written worker sections** from meta.yaml lead prompts.

### Phase 3: Build-Time Injection (workers)

**`inject_scope_and_siblings()`** — add to `generate.py`:

For each worker agent, inject:
```markdown

## Scope & Siblings
You handle: {routes}
Your siblings:
- {sibling_name}: {sibling_routes}

If work is outside your scope, state what you handle and name the correct sibling.
Do NOT attempt out-of-scope work.
```

**`inject_project_commands()`** — from crew.yaml `components.verification.checks`:
```markdown

## Project Commands
- Build: {build_cmd}
- Test: {test_cmd}
- Lint: {lint_cmd}
```

### Phase 4: Eval Context Simulation

**Problem:** Our evals invoke agents via `kiro-cli chat --agent X`. Kiro-cli loads the agent's resources and skills. But we don't measure or validate the context load.

**Solution:**

1. Add `--measure-context` flag to eval harness that runs `/context` after agent spawn to capture token usage
2. Store context metrics in `meta.json`:
   ```json
   "context_budget": {
     "dispatcher": {"prompt_tokens": 450, "resources_tokens": 2100, "total": 2550},
     "crew-augmenter": {"prompt_tokens": 800, "resources_tokens": 3200, "total": 4000}
   }
   ```
3. Add budget threshold warning: flag agents exceeding 8K total static tokens

**Reference project:** Create `examples/eval-reference/` with:
- Fixed `.crews/crew.yaml` (known config)
- Pre-generated `.kiro/agents/` (stable baseline)
- Used by evals for reproducible context testing

### Phase 5: Dispatcher Scope Boundary

Inject scope boundary into dispatcher prompt (same logic orchestrators already get):
```markdown

## Scope Boundary
Do NOT attempt work in these areas — delegate instead:
- target-project-features
- target-project-bugs
- infrastructure
- deployments
```

## File Changes Summary

| File | Change |
|------|--------|
| `shared/skills/verification-protocol/SKILL.md` | NEW — from steering/worker/verification.md |
| `shared/skills/git-protocol/SKILL.md` | NEW — from steering/worker/git.md |
| `shared/skills/troubleshooting-protocol/SKILL.md` | NEW — from steering/worker/troubleshooting.md |
| `shared/skills/completion-protocol/SKILL.md` | NEW — from steering/universal/completion.md |
| `generate.py` | Add inject_worker_context(), inject_scope_and_siblings(), inject_project_commands() |
| `generate.py` | Add protocol skills to worker/orchestrator resources |
| `base/crews/*.yaml` | Remove `read` from orchestrator tool lists |
| `base/crews/meta.yaml` | Remove hand-written worker sections from lead prompts |
| `scripts/eval-crew.py` | Add --measure-context flag |

## Validation Criteria

1. `just build` produces valid JSON for all agents
2. No agent exceeds 8K tokens of static context (prompt + resources)
3. Routing evals pass at same or better rate (leads still know their workers)
4. Execution evals improve (workers now have verification protocol available)
5. Skills load on-demand (verify with `/context show` in a test session)

## Risks

| Risk | Mitigation |
|------|------------|
| Skills not triggering when needed | Skill descriptions must be precise — test with `/context show` |
| Injected tables make prompts too long | Monitor token counts; tables are compact (~50 tokens per worker) |
| Removing `read` from leads breaks something | Leads already work without read (general-lead has no read today) |
| Protocol skills conflict with prompt instructions | Skills supplement, not override — prompt is authoritative |

## Sequence

```
Phase 1 (skills)     → immediate value, no breaking changes
Phase 2 (leads)      → depends on Phase 1 (leads reference skills)
Phase 3 (workers)    → independent of Phase 2
Phase 4 (eval)       → after Phases 1-3 stabilize
Phase 5 (dispatcher) → trivial, do alongside Phase 2
```

Phase 1 is safe to ship independently — it only adds resources, doesn't remove anything.
