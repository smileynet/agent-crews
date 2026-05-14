---
name: crew-structural-rules
description: Structural invariants for agent crews. Use when building, modifying, or auditing crew configurations to ensure tool scoping, context budget, and delegation boundaries are correct.
---

# Crew Structural Rules

## Tool Scoping

| Agent type | Allowed tools | Forbidden |
|-----------|---------------|-----------|
| Orchestrator | `read`, `subagent`, `todo_list` | `write`, `shell`, `glob`, `grep` |
| Worker | `read`, `write`, `shell`, `glob`, `grep`, search tools | `subagent` |

**Why:** "Behavioral constraints are suggestions; tool availability is enforcement." (AutonomousAICapabilities lessons-learned)

## Subagent Scoping

Orchestrators get:
- `availableAgents`: list of own crew's workers (visibility)
- `trustedAgents`: same list (auto-approval, no permission prompt)

Workers NEVER get subagent. If blocked, they report `## BLOCKED: [reason]` upward.

## Context Budget

Steering files with `inclusion: always` load every turn. Budget rules:
- Each file: < 50 lines
- Total always-on steering: < 250 lines
- Templates, examples, report formats → skills (on-demand)
- Rules and principles → steering (always-on)

## Crew YAML Structure

```yaml
# Global tools (inherited by workers, NOT orchestrators)
tools:
  - read
  - write
  - shell
  # NO subagent here — only in orchestrator archetype

architypes:
  - type: orchestrator
    tools:           # REPLACES global tools
      - read
      - subagent
      - todo_list
    agents: [...]

  - type: worker     # Inherits global tools (no subagent)
    agents: [...]
```

## Validation Checklist

After any crew change, verify:
```bash
python3 -c "
import json, os
agents_dir = 'base/agents'
orchestrators = ['raid-leader','commander','sage','crew-chief','handler','dungeon-master','ashen-one']
for f in os.listdir(agents_dir):
    if not f.endswith('.json'): continue
    name = f[:-5]
    with open(os.path.join(agents_dir, f)) as fh:
        d = json.load(fh)
    tools = d.get('tools', [])
    if name in orchestrators:
        assert 'write' not in tools, f'{name} has write'
        assert 'shell' not in tools, f'{name} has shell'
    else:
        assert 'subagent' not in tools, f'{name} has subagent'
print('✅ All structural invariants pass')
"
```

## Steering File Conventions

| Type | Where | When loaded |
|------|-------|-------------|
| Rules (always apply) | `steering/*.md` with `inclusion: always` | Every turn |
| Templates/procedures | `skills/*/SKILL.md` | On demand (when task matches description) |
| Prompts (user-invoked) | `prompts/*.md` | When user types `@prompt-name` |
