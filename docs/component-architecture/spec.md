# Component Architecture Specification

**Version:** 1.0
**Date:** 2026-05-11
**Decisions:** D-001 through D-036, I-001 through I-016

---

## 1. Problem Statement

Cross-cutting behavioral concerns (signaling, verification, troubleshooting, git workflow, etc.) are currently copy-pasted across 8 base crew YAMLs and 3 custom project crews. Changes to a behavioral rule require editing every crew file. Drift is inevitable. New projects inherit stale patterns.

## 2. Goal

Extract cross-cutting concerns into composable, named, version-controlled components. The generator reads component declarations and assembles complete agent configurations. Changing a behavioral rule means editing one file and regenerating.

## 3. Architecture

### 3.1 Layer Model

```
Layer 4: Agent Identity     (prompt file — per-agent, unique)
Layer 3: Project Config     (crew.yaml components: section — per-project overrides)
Layer 2: Fleet Defaults     (fleet.yaml defaults: — shared baseline)
Layer 1: Components         (shared/components/ — behavioral building blocks)
```

### 3.2 Delivery Mechanisms

| Content Type | Delivery | Why |
|---|---|---|
| Agent identity, scope, delegation, routing, theme | `prompt` field (file:// URI → `.kiro/prompts/<agent>.md`) | Per-agent, unique |
| Behavioral rules for workers | Steering files in `.kiro/steering/worker/` | Inherited by subagents, no prompt bloat |
| Behavioral rules for orchestrators | Steering files in `.kiro/steering/orchestrator/` | Separate from worker rules, no context pollution |
| Behavioral rules for all agents | Steering files in `.kiro/steering/universal/` | Shared baseline |
| On-demand knowledge | Skills in `.kiro/skills/` | Loaded only when relevant |

### 3.3 Resource Globs Per Agent Type

```json
// Orchestrator
"resources": [
  "file://.kiro/steering/universal/*.md",
  "file://.kiro/steering/orchestrator/*.md",
  "skill://.kiro/skills/**/SKILL.md"
]

// Worker
"resources": [
  "file://.kiro/steering/universal/*.md",
  "file://.kiro/steering/worker/*.md",
  "skill://.kiro/skills/**/SKILL.md"
]

// Verifier/Editor (intentionally no steering — fresh judgment)
"resources": []
```

---

## 4. Component System

### 4.1 Component File Format

Each component is a structured YAML file at `shared/components/<name>/<variant>.yaml`:

```yaml
name: <component>-<variant>
description: "<one-line description>"
targets: [worker]                    # worker | orchestrator | all

prompt: |                            # injected into prompt .md (orchestrator-targeted only)
  ## <Section>
  <content>

allowed_commands:                    # merged into execute_bash.allowedCommands
  - "git *"

resources:                           # merged into agent resources
  - "skill://.kiro/skills/<name>.md"

hooks:                               # merged into agent hooks
  postToolUse:
    - matcher: "fs_write"
      command: "<command>"
      timeout_ms: 30000

steering: |                          # written as .kiro/steering/{target}/<component>.md
  ---
  inclusion: always
  ---
  # <Title>
  <behavioral rules>

subagents:                           # generates additional agent .json files
  - name: <name>
    description: "<desc>"
    tools: ["read", "shell"]
    prompt: |
      <subagent prompt>
```

### 4.2 Component Inventory

| Component | Variants | Type | Target |
|---|---|---|---|
| **Signaling** | standard, minimal, tracked | Selectable | all |
| **Sanity Gate** | assumption-register | Single | all |
| **Search** | layered | Compositional (sources, priority, conflict) | worker |
| **Memory** | four-tier | Compositional (tiers, discovery) | orchestrator |
| **Notifications** | channels | Compositional (channels, policy) | orchestrator |
| **Task Tracking** | soft-hard | Selectable backend (todo-tool, beads, github-issues, flat-file) | orchestrator |
| **Decisions** | progressive, upfront, minimal | Selectable | orchestrator |
| **Handoff** | scope-based | Auto-generated from crew scope | orchestrator |
| **Narration** | verified, evidence, self-report | Selectable | orchestrator |
| **Troubleshooting** | systematic | Single + configurable escalation | worker |
| **Writing** | standard | Compositional (editor triggers, theme) | worker |
| **Verification** | gate | Compositional (checks, task types) | worker |
| **Git** | checkpoint, pr-based, manual | Selectable + worktrees toggle | worker |
| **Completion** | standard, minimal, full | Selectable + custom handoff elements | all |

### 4.3 Component Dependencies

Convention-based (implicit from structure). No explicit dependency graph.
- `subagents:` field → generator produces those agents
- `resources:` field → generator ensures files exist
- `allowed_commands:` field → generator merges into toolsSettings

Explicit `requires:` only added if implicit doesn't work (Terraform "last resort" principle).

---

## 5. Configuration

### 5.1 Fleet Configuration

```yaml
# fleet.yaml (committed — project registry + defaults)
defaults:
  persona: personal
  components:
    signaling: standard
    sanity_gate: assumption-register
    search: { variant: layered, sources: [local, web], priority: "local → web", conflict: first-authoritative }
    memory: { variant: four-tier, tiers: [working, session], discovery: false }
    notifications: { variant: channels, channels: [toast], policy: completions }
    task_tracking: { variant: soft-hard, backend: todo-tool }
    decisions: progressive
    handoff: scope-based
    narration: verified
    troubleshooting: { variant: systematic, escalation: { same_approach: 2, strategies: 3, action: ask-user } }
    writing: { variant: standard, editor: { triggers: [new-document, significant-revision, user-facing] }, theme: null }
    verification: { variant: gate, checks: { build: null, test: null, lint: null } }
    git: { variant: checkpoint, worktrees: false }
    completion: { variant: standard, followups: file-issues }

projects:
  ferris-tracker:
    type: custom
    theme: nautical
  taskflow-ui:
    type: custom
    theme: expedition
  pixel-dungeon:
    type: themed
    theme: ocean
```

```yaml
# fleet.local.yaml (gitignored — per-machine)
deployments:
  ferris-tracker: C:\Users\dev\code\ferris-tracker
  taskflow-ui: C:\Users\dev\code\taskflow-ui
```

### 5.2 Project Component Configuration

```yaml
# projects/<name>/.kiro/crew.yaml — components: section
# Only declares OVERRIDES. Everything else comes from fleet defaults.
components:
  verification:
    checks:
      build: "cargo check"
      test: "cargo test"
      lint: "cargo clippy"
  git:
    workflow: pr-based
  completion:
    handoff:
      include: [asked-delivered, wrong-turns, decisions, next-steps, context]
```

### 5.3 Crew Scope Declarations

```yaml
# base/crews/bug-hunt.yaml
scope:
  handles: [bugs, testing, debugging, test-coverage]
  refuses: [features, infrastructure, research]
```

Generator reads all crew scopes in a project and builds routing tables for orchestrators.

### 5.4 Theme Specification

```yaml
# projects/<name>/.kiro/theme.yaml
name: nautical
domain: "Age of sail, exploration, maritime navigation"
vocabulary:
  use: [chart, navigate, sail, anchor, reef, horizon, crew, captain]
  avoid: [drive, road, highway, land-based metaphors]
tone: "Confident but not pirate-campy. Professional sailor, not Jack Sparrow."
examples:
  - "Charting a course through the auth module. Two reefs spotted."
  - "Anchoring this branch — all tests pass, ready for port."
anti-examples:
  - "Arr matey! Shiver me timbers, there be bugs!"
  - "Navigating the ever-evolving landscape of..."
```

Applies to: narration, notifications, handoff redirects, welcome messages.
Does NOT apply to: committed artifacts (docs, PRs, commits, ADRs).

---

## 6. Generator Behavior

### 6.1 Resolution Chain

```
fleet.yaml defaults → project crew.yaml overrides → shared/components/<name>/<variant>.yaml
```

### 6.2 Generation Steps

For each project:

1. **Load config:** Read fleet defaults, merge project crew.yaml overrides
2. **Load components:** For each declared component, load the YAML file from `shared/components/`
3. **Substitute placeholders:** Replace `{{key}}` in prompt/commands/steering with project config values
4. **Filter by target:** Separate components into orchestrator-targeted and worker-targeted
5. **Assemble prompts:** Write `.kiro/prompts/<agent>.md` files (identity + delegation + orchestrator component fragments)
6. **Write steering:** Write `.kiro/steering/{universal,orchestrator,worker}/<component>.md` from component `steering:` fields
7. **Generate agent JSON:** For each agent, produce `.json` with:
   - `"prompt": "file://.kiro/prompts/<agent>.md"`
   - `resources` glob for agent type
   - Merged `toolsSettings` (allowed_commands + denied_commands + denied_paths)
   - Merged `hooks`
   - Tools list
8. **Generate subagents:** From component `subagents:` fields, produce verifier.json, editor.json
9. **Generate routing table:** Read all crew scopes, build handoff routing, inject into orchestrator prompts
10. **Copy skills:** Ensure referenced skills exist in `.kiro/skills/`

### 6.3 Safety Settings (standard for all workers)

```json
{
  "toolsSettings": {
    "execute_bash": {
      "deniedCommands": ["rm -rf *", "git push --force*", "git reset --hard*", "git clean -f*"],
      "autoAllowReadonly": true
    },
    "fs_write": {
      "allowedPaths": ["./**"],
      "deniedPaths": [".kiro/agents/**", ".kiro/steering/**", ".kiro/settings/**"]
    }
  }
}
```

### 6.4 Staleness Check

`just check` compares modification times:
- Source: `shared/components/**/*.yaml`, `fleet.yaml`, `base/crews/*.yaml`, project `crew.yaml`
- Output: `.kiro/agents/*.json`, `.kiro/prompts/*.md`, `.kiro/steering/**/*.md`

If any source is newer than output → project is stale.

---

## 7. Generated Output Structure

```
projects/<name>/.kiro/
├── agents/
│   ├── <orchestrator>.json
│   ├── <worker-1>.json
│   ├── <worker-2>.json
│   ├── verifier.json              # if narration: verified
│   └── editor.json                # if writing.editor.triggers non-empty
├── prompts/
│   ├── <orchestrator>.md          # identity + delegation + routing + theme
│   ├── <worker-1>.md             # identity + specialization
│   └── ...
├── steering/
│   ├── universal/                 # loaded by all agents
│   │   ├── signaling.md
│   │   ├── sanity-gate.md
│   │   └── completion.md
│   ├── orchestrator/              # loaded by orchestrators only
│   │   ├── narration.md
│   │   ├── handoff.md
│   │   ├── task-tracking.md
│   │   ├── decisions.md
│   │   ├── memory.md
│   │   └── notifications.md
│   └── worker/                    # loaded by workers only
│       ├── troubleshooting.md
│       ├── verification.md
│       ├── git.md
│       └── writing.md
├── skills/
│   └── writing-style/SKILL.md
├── prompts/
│   └── crew-sheet.md
└── theme.yaml                     # optional
```

---

## 8. Behavioral Specifications

### 8.1 Signaling (D-016/017)

| Variant | Statuses | Fields |
|---|---|---|
| standard | DONE/PARTIAL/BLOCKED/FAILED | Task, Result, Evidence, Remaining, Assumptions |
| minimal | DONE/BLOCKED | (none) |
| tracked | DONE/PARTIAL/BLOCKED/FAILED | standard + Issue IDs |

### 8.2 Sanity Gate (D-018)

Assumption register pattern:
- Generate questions upfront
- Track answered vs assumed
- Surface assumptions in DONE signal
- Rubber-stamp guard: pause after 3 consecutive agent-suggested decisions

### 8.3 Search (D-019/020)

Compositional. Project declares:
- `sources`: additive list (local, web, cached-docs, MCP servers)
- `priority`: resolution order
- `conflict`: first-authoritative | merge | ask-user

Default: `sources: [local, web], priority: "local → web", conflict: first-authoritative`

### 8.4 Memory (D-021/022/023)

Compositional tiers:
- `working` (.scratch/) — always needed
- `session` (.scratch/session/) — within-session persistence
- `episodic` (.kiro/memory/lessons.md) — cross-session learnings
- `semantic` (ADRs, steering, research) — permanent knowledge

Default: `tiers: [working, session], discovery: false`

### 8.5 Notifications (D-025)

Compositional:
- `channels`: toast | discord | slack | email (additive)
- `policy`: completions | verbose | silent

Default: `channels: [toast], policy: completions`

### 8.6 Task Tracking (D-026/027)

Fixed methodology (soft planning patterns available in any order) + selectable backend:
- `todo-tool` (default) — kiro built-in
- `beads` — bd CLI
- `github-issues` — gh CLI
- `flat-file` — .scratch/tasks.md

### 8.7 Decisions (D-028/029)

Selectable:
- `progressive` (default) — capture → log → ADR, nudge not enforce
- `upfront` — spec/PRD before implementation
- `minimal` — capture only, no formal log

### 8.8 Handoff (D-030)

Auto-generated from crew `scope: { handles, refuses }` declarations. Generator builds routing table + refusal rules. No user configuration.

### 8.9 Narration (D-031)

Selectable grounding:
- `verified` (default) — verifier subagent (fresh context) confirms claims
- `evidence` — deterministic checks only (build/test/lint pass)
- `self-report` — no verification (research, planning)

Verifier sees: original task + final output. NOT worker reasoning.

### 8.10 Troubleshooting (D-032)

Four-phase methodology (invariant):
1. Investigate (five-whys, call-chain, boundary diagnostics, bisect, diff)
2. Pattern Analysis (good-vs-bad, reference impl, evidence ladder, reduction, triage)
3. Hypothesis (single, with evidence, one variable, predict-then-verify)
4. Fix (failing test first, single fix, verify all pass)

Configurable escalation:
- `same_approach`: N (default 2) — same approach fails N times → change strategy
- `strategies`: N (default 3) — N strategies fail → escalate
- `action`: ask-user | report-failed

### 8.11 Writing (D-033)

- Style: reference to writing-style skill
- Editor: independent subagent (fresh context), triggers on new-document / significant-revision (>5 lines) / user-facing
- Theme: if theme.yaml exists, inject into narration/notifications

Editor sees: document + style rules. NOT drafting agent reasoning. Returns: specific edits or "clean".

### 8.12 Verification (D-034)

Gate workflow (mandatory, all task types): identify → run → read → verify → claim.

14 task types with specific checks:
- code: [build, test, lint, scope]
- infrastructure: [plan-review, scope]
- config: [build, smoke]
- writing: [editor, style-check, links, accuracy]
- research: [sources, traceability, completeness]
- product_design: [walkthrough, completeness, coherence, jtbd-alignment]
- architecture: [assumptions, alternatives, consequences]
- ui_ux: [spec-compliance, accessibility, responsive, states]
- deployment: [health, smoke, logs]
- data_migration: [integrity, before-after, rollback]
- testing: [coverage, edge-cases, red-green]
- refactoring: [behavior-preservation]
- planning: [completeness, actionability, dependencies]
- security: [threat-model, owasp, secrets, permissions]

Project-specific commands via `checks: { build, test, lint }`.
`skip_types` and `explicit_types` for overrides.

### 8.13 Git (D-035)

Selectable workflow:
- `checkpoint` (default) — commit frequently, push immediately, direct to branch
- `pr-based` — feature branch, PR to merge, never touch main
- `manual` — commit locally, never push

Optional: `worktrees: true` for parallel agent isolation.

Invariants (all workflows): meaningful messages, commit before risky ops, commit after working states, only commit after verification, explicit staging, no force-push without permission.

### 8.14 Completion (D-036)

Sequence: verification → git → signaling → followups → handoff → notifications → memory.

Followups: `file-issues` (default) | `inline` | `none`

Handoff presets:
- `minimal`: asked-delivered, files, next-steps
- `standard` (default): asked-delivered, state-change, files, issues-filed, next-steps
- `full`: all 10 elements
- Custom: explicit `include:` list

10 handoff elements: asked-delivered, state-change, files, problems, wrong-turns, decisions, issues-filed, next-steps, context, verification.

---

## 9. Migration Strategy

1. Implement component system in generator (no legacy path)
2. Generate output for ferris-tracker (custom, low risk)
3. Diff against current output — fix semantic differences
4. Cut over all projects
5. Strip inline cross-cutting content from crew YAMLs
6. Add `scope:` declarations to all crew YAMLs

---

## 10. Success Criteria

- [ ] `just build` produces working agent JSON from component-based configuration
- [ ] No cross-cutting content duplicated across crew YAMLs
- [ ] Adding a new project = declare components in crew.yaml + run generator
- [ ] Changing a component = edit one file, regenerate all
- [ ] Verifier and editor run as independent subagents with fresh context (no steering loaded)
- [ ] Theme changes isolated to theme.yaml
- [ ] All existing projects continue to work (no behavioral regression)
- [ ] Workers cannot modify .kiro/agents/ or .kiro/steering/ (deniedPaths)
- [ ] Workers cannot force-push or destructive-delete (deniedCommands)
- [ ] `just check` reports stale projects accurately
- [ ] Each component file individually version-controlled and diffable

---

## 11. Testing Plan

### 11.1 Diff Validation
- Generate with new system, diff against current output
- Semantic equivalence (same behavioral rules, possibly different structure)

### 11.2 Subagent Inheritance Test
- Confirm dispatched subagent loads its OWN .json resources, not parent's
- Confirm verifier/editor get NO steering (fresh judgment)

### 11.3 Steering Isolation Test
- Confirm orchestrator does NOT see worker steering
- Confirm worker does NOT see orchestrator steering
- Confirm both see universal steering

### 11.4 End-to-End Smoke Test
- Dispatch a worker via orchestrator
- Worker reports DONE with verification evidence
- Orchestrator dispatches verifier
- Verifier confirms or rejects
- Completion sequence fires correctly

---

## 12. Open Items

- Subagent resource inheritance needs empirical testing (I-001 flag)
- Knowledge base resources (indexType, autoUpdate) — available but not yet used by any component
- Hook `cache_ttl_seconds` — available but no current use case
