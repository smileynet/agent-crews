# Implementation Spec: Auto-Generated Dispatcher & Shared Utilities

## References
- [ADR-008: Auto-Generated Project Dispatcher](../decisions/ADR-008-auto-generated-dispatcher.md)
- [ADR-009: Shared Utility Agents](../decisions/ADR-009-shared-utility-agents.md)
- [Meta Crew Rework Proposal](../proposals/meta-crew-rework.md)

## Overview

Three coordinated changes:
1. Generator synthesizes a project-level dispatcher from crew composition
2. `shared: true` flag on agents makes them accessible to all orchestrators
3. Meta crew removes its dispatcher, follows standard crew pattern

## Phase 1: Shared Utility Agents

### 1.1 YAML Schema Change

Add `shared` field to agent definitions:

```yaml
# base/crews/bug-fix.yaml
agents:
  - name: verifier
    shared: true
    description: "..."
```

**Files to modify:**
- `base/crews/bug-fix.yaml` — add `shared: true` to verifier
- `base/crews/research.yaml` — add `shared: true` to editor
- `base/crews/meta.yaml` — add `shared: true` to kiro-helper

### 1.2 Generator: Collect Shared Agents

After generating all crews for a project, collect shared agent names:

```python
def collect_shared_agents(crew_files: list[Path]) -> list[str]:
    """Collect agent names marked shared: true across all crews."""
    shared = []
    for cf in crew_files:
        crew = yaml.safe_load(cf.read_text())
        for archetype in crew.get("architypes", []):
            for agent in archetype.get("agents", []):
                if agent.get("shared"):
                    shared.append(agent["name"])
    return shared
```

### 1.3 Generator: Inject Shared Agents

Use existing `inject_subagents_into_orchestrators()` function (already implemented in meta crew rework). Call it with shared agent names after all crews are generated.

**Integration points** (all code paths that generate agents for a project):
- `generate_all()` — self-hosted path (line ~835)
- Single-project path (line ~1600)
- fleet.local.yaml path (line ~875)

### 1.4 Generator: Deduplication with Component Subagents

In `generate_subagents()`, skip if agent file already exists:

```python
out_path = agents_dir / f"{sub['name']}.json"
if out_path.exists():
    continue  # crew-defined version wins
```

## Phase 2: Auto-Generated Dispatcher

### 2.1 Remove Dispatcher from Meta Crew

**File:** `base/crews/meta.yaml`

Remove the entire `- type: dispatcher` archetype block (lines 45-160 approximately). The dispatcher agent definition, its prompt, routing table, welcome message — all removed.

The meta crew becomes:
```yaml
architypes:
  - type: orchestrator  # build-lead
  - type: orchestrator  # ops-lead
  - type: worker        # crew-creator, crew-augmenter, crew-researcher, ...
  - type: orchestrator  # bugfix-lead
  - type: worker        # meta-debugger, meta-tester
```

### 2.2 Move crew-releaser Under ops-lead

**File:** `base/crews/meta.yaml`

Add `crew-releaser` to ops-lead's explicit `availableAgents`:
```yaml
- name: ops-lead
  toolsSettings:
    subagent:
      availableAgents: [crew-analyst, crew-doctor, crew-validator, project-hygiene, crew-releaser]
```

### 2.3 Generator: Synthesize Dispatcher

New function in `generate.py`:

```python
def synthesize_dispatcher(
    leads: list[dict],        # [{name, description, routes, crew}]
    shared_agents: list[str], # [verifier, editor, kiro-helper]
    kiro_dir: Path,
    dispatcher_config: dict,  # from .crews/crew.yaml dispatcher: section
    dry_run: bool = False
) -> dict:
    """Auto-generate a project dispatcher from crew composition."""
```

**Inputs:**
- `leads` — collected from all `type: orchestrator` agents across crews
- `shared_agents` — collected from `shared: true` agents
- `dispatcher_config` — optional overrides from `.crews/crew.yaml`

**Output:** A complete agent JSON written to `.kiro/agents/dispatcher.json`

### 2.4 Dispatcher Prompt Template

```python
DISPATCHER_PROMPT_TEMPLATE = """You are dispatcher — the project orchestrator.

## Self-Execute Heuristic
BEFORE checking the routing table: can this be done in ≤1 tool call with no prior reading?
If YES → execute directly (run command, write file, check status).
If NO → plan and delegate.

Examples of self-execute:
- "run tests" → shell: <test command>
- "git status" → shell: git status
- "write this content to path" → write the file

Everything else MUST be delegated to a crew lead.

## Planning Protocol
For any request that involves multiple steps:
1. Review available crews and their capabilities
2. Identify which leads are needed and in what sequence
3. Build a task graph (what depends on what)
4. Dispatch to leads in dependency order
5. Track progress and report results

Do NOT attempt multi-step work yourself. Your job is to PLAN and DELEGATE.
Even if you could do it, a lead will do it better — they have specialized workers.

## Routing Table

{routing_table}

## Shared Utilities
Available to dispatch directly for one-shot tasks:
{shared_utilities}

## Delegation Format
Always include:
- agentName: exact agent name
- task: clear description of what to achieve
- context: relevant details from user request

## Rules
- Atomic task (≤1 tool call) → self-execute
- One-shot utility task → dispatch to shared utility directly
- Everything else → dispatch to the appropriate crew lead
- Multi-crew work → plan the sequence, dispatch leads in order
- Never do specialist work yourself
- Always narrate: "Delegating to X because Y"
{prompt_suffix}"""
```

### 2.5 Routing Table Generation

Built from each lead's `routes:` and `description` fields:

```python
def build_routing_table(leads: list[dict]) -> str:
    lines = ["| Crew Lead | Send work when... |",
             "|-----------|-------------------|"]
    for lead in leads:
        lines.append(f"| {lead['name']} | {lead['routes']} |")
    return "\n".join(lines)
```

### 2.6 Welcome Message Generation

```python
def build_welcome_message(leads: list[dict], shared: list[str]) -> str:
    lines = ["🎯 Dispatcher ready. What are we working on?\n"]
    lines.append("Available crews:")
    for lead in leads:
        desc = lead.get('description', lead['routes'])
        lines.append(f"- {desc} → {lead['name']}")
    lines.append("")
    if shared:
        lines.append(f"Utilities: {', '.join(shared)}")
        lines.append("")
    lines.append("Or just tell me what to do — simple tasks I'll handle directly.")
    return "\n".join(lines)
```

Prompts are appended automatically by the existing generator logic (it already scans `.kiro/prompts/`).

### 2.7 Dispatcher Config Schema

In `.crews/crew.yaml`:

```yaml
dispatcher:
  include_meta: false        # Add meta crew agents to routing (default: false)
  include_kiro_helper: true  # Add kiro-helper as shared utility (default: false)
  prompt_suffix: |           # Appended to generated prompt
    ## Project-Specific Rules
    ...
  keyboard_shortcut: ctrl+shift+d  # Default: ctrl+shift+d
```

All fields optional. Absent `dispatcher:` section = fully auto-generated with defaults.

### 2.8 Integration into Generator Pipeline

The dispatcher is synthesized AFTER all crews are generated (so all leads are known):

```
1. Generate all crew agents (leads + workers)
2. Collect shared agents
3. Inject shared agents into orchestrators
4. Synthesize dispatcher (from leads + shared + config)
5. Generate component subagents (skip if crew version exists)
6. Inject component subagents into orchestrators (including dispatcher)
```

## Phase 3: AGENTS.md Management

### 3.1 Marker-Based Insertion

The generator manages specific sections of AGENTS.md between markers:

```markdown
<!-- CREW-AGENTS START -->
See `@crew-sheet` for the full agent roster, prompts, and commands.

| Crew | Lead | Workers |
|------|------|---------|
| General | general-lead | planner, explorer, researcher, ... |
| Bug Fix | bugfix-lead | triager, investigator, fixer, verifier |
...
<!-- CREW-AGENTS END -->
```

**Rules:**
- Only content between markers is modified
- Content outside markers is never touched
- If markers don't exist, append the section at the end
- Idempotent — running twice produces same result

### 3.2 Generator Integration

Add to the post-generation pipeline (after crew-sheet generation):

```python
def update_agents_md(kiro_dir: Path, leads: list[dict], crews_dir: Path):
    """Update AGENTS.md crew section between markers."""
    agents_md = kiro_dir.parent / "AGENTS.md"
    if not agents_md.exists():
        return  # Don't create AGENTS.md, only update existing
    # ... marker-based insertion logic
```

## Phase 4: Meta Crew Specific Changes

### 4.1 Summary of meta.yaml Changes

| Change | What |
|--------|------|
| Remove `type: dispatcher` block | ~120 lines removed |
| Move crew-releaser to ops-lead workers | Update ops-lead `availableAgents` |
| Add `shared: true` to kiro-helper | One field addition |
| Remove kiro-helper/crew-releaser from dispatcher routing | N/A — dispatcher block removed |

### 4.2 Self-Hosted Behavior

The `self_hosted: true` flag in fleet.yaml no longer needs special dispatcher handling. The auto-generated dispatcher works the same for all projects. The flag may still be useful for other purposes (output to repo root `.kiro/` instead of `projects/`).

## Testing Plan

### Unit Verification

```bash
# After implementation, verify:

# 1. Auto-generated dispatcher exists and routes to leads
just build agent-crews
python3 -c "
import json
d = json.load(open('.kiro/agents/dispatcher.json'))
print('Routes to:', d['toolsSettings']['subagent']['availableAgents'])
# Should show: [build-lead, ops-lead, bugfix-lead, verifier, editor, kiro-helper]
"

# 2. Shared agents accessible to all leads
python3 -c "
import json
for name in ['build-lead', 'ops-lead', 'bugfix-lead']:
    d = json.load(open(f'.kiro/agents/{name}.json'))
    avail = d['toolsSettings']['subagent']['availableAgents']
    assert 'verifier' in avail, f'{name} missing verifier'
    assert 'editor' in avail, f'{name} missing editor'
    assert 'kiro-helper' in avail, f'{name} missing kiro-helper'
print('All leads have shared utilities ✅')
"

# 3. Examples get correct dispatcher
just build examples/rust-cli/.kiro/crew.yaml
python3 -c "
import json
d = json.load(open('examples/rust-cli/.kiro/agents/dispatcher.json'))
avail = d['toolsSettings']['subagent']['availableAgents']
assert 'general-lead' in avail
assert 'bugfix-lead' in avail
assert 'verifier' in avail
print('Example dispatcher routes correctly ✅')
"

# 4. Deduplication works
# rust-cli has bug-fix crew (defines verifier) + components
# Should have ONE verifier.json (crew version, not component version)
python3 -c "
import json
d = json.load(open('examples/rust-cli/.kiro/agents/verifier.json'))
assert 'testing-patterns' in str(d.get('resources', []))  # crew version has skills
print('Deduplication works ✅')
"

# 5. No dispatcher in any crew YAML
grep -r 'type: dispatcher' base/crews/
# Should return nothing
```

### Regression Checks

```bash
# All examples still generate without errors
for ex in examples/*/; do
  if [ -f "$ex/.kiro/crew.yaml" ]; then
    uv run generate.py "$ex/.kiro/crew.yaml" || echo "FAILED: $ex"
  fi
done

# Hierarchy validation still passes (no workers with subagent)
just build agent-crews  # exits 0

# Existing evals still pass
just eval agent-crews
```

## Implementation Order

| Step | What | Files | Risk |
|------|------|-------|------|
| 1 | Add `shared: true` to verifier, editor, kiro-helper | 3 crew YAMLs | Low |
| 2 | Implement `collect_shared_agents()` + injection in all code paths | generate.py | Medium |
| 3 | Add deduplication to `generate_subagents()` | generate.py | Low |
| 4 | Implement `synthesize_dispatcher()` + prompt template | generate.py | Medium |
| 5 | Remove dispatcher from meta.yaml, move crew-releaser | meta.yaml | Medium |
| 6 | Wire dispatcher synthesis into all generation paths | generate.py | Medium |
| 7 | Implement AGENTS.md marker-based update | generate.py | Low |
| 8 | Regenerate all projects + examples | — | Low |
| 9 | Update AGENTS.md for this repo | AGENTS.md | Low |
| 10 | Run tests, verify, commit | — | — |

Steps 1-3 can be committed independently (shared utilities work without dispatcher changes).
Steps 4-6 are interdependent (dispatcher synthesis requires removing old dispatcher).
Steps 7-9 are cleanup.

## Commit Strategy

1. `feat: shared utility agents (shared: true flag)` — Steps 1-3
2. `feat: auto-generated project dispatcher (ADR-008)` — Steps 4-6
3. `docs: AGENTS.md marker-based management` — Steps 7-9

## Backlog Items (deferred)

- Config complexity review / simplification (meta.yaml prompt extraction)
- Move backlog to GitHub issues
- Cross-crew scoping for non-shared agents (if needed — monitor after shared utilities ship)
- Eval baseline measurement (2 weeks post-deployment)
