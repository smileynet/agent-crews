---
name: kiro-cli-schema
description: "Kiro CLI agent JSON schema, valid fields, tool mappings, hooks, and common mistakes. Use when creating or modifying crew YAML or agent configurations."
---

# Kiro CLI Schema Reference

## Agent JSON — Valid Top-Level Fields

```json
{
  "name": "string (required)",
  "description": "string",
  "prompt": "string | file:// URI",
  "tools": ["tool-name"],
  "allowedTools": ["tool-name"],
  "toolsSettings": { "canonical_name": {} },
  "resources": ["file://path", "skill://path"],
  "hooks": { "hookType": [{ "command": "...", "matcher": "..." }] },
  "mcpServers": { "serverName": { "command": "...", "args": [], "env": {} } },
  "keyboardShortcut": "modifier+key",
  "welcomeMessage": "string"
}
```

## Tool Name Mapping

| Canonical (use in toolsSettings) | Aliases (valid in tools/allowedTools) |
|----------------------------------|---------------------------------------|
| `fs_read` | `read`, `fsRead` |
| `fs_write` | `write`, `fsWrite` |
| `execute_bash` | `shell`, `execute_cmd` |
| `crew` | `subagent`, `agent_crew`, `use_subagent` |
| `todo_list` | `task`, `todo` |

**Rule**: `toolsSettings` keys MUST use canonical names.

## toolsSettings — Valid Fields

```yaml
fs_write:
  allowedPaths: ["src/**"]
  deniedPaths: ["node_modules/**"]

execute_bash:
  allowedCommands: ["git *", "npm test"]
  deniedCommands: ["rm -rf *"]
  autoAllowReadonly: true

crew:
  availableAgents: ["researcher", "builder"]  # supports globs
  trustedAgents: ["researcher", "builder"]    # auto-approved
```

## Hooks

| Hook | When | matcher required? | Notes |
|------|------|:-----------------:|-------|
| `agentSpawn` | Session start | No | Output injected into context |
| `stop` | After every response | No | Keep fast (<2s) |
| `postToolUse` | After specific tool | Yes | Good for auto-lint |
| `preToolUse` | Before specific tool | Yes | Exit 2 = block call |

Environment: `$KIRO_FILE_PATH` available in `fs_write` matcher hooks.

## Resources

```yaml
resources:
  - file://.kiro/steering/**/*.md       # always loaded (glob)
  - skill://.kiro/skills/my-skill.md    # loaded on keyword trigger
```

## crew.yaml Structure

```yaml
workflow: crew-name
architypes:                    # NOTE: spelling is "architypes" (not "archetypes")
  - type: orchestrator         # orchestrator | worker
    tools: [read, subagent]
    prompt: |
      Archetype-level prompt
    agents:
      - name: agent-name
        description: ""
        keyboardShortcut: "ctrl+shift+x"
        welcomeMessage: ""
        prompt: |
          Agent-level prompt (appended to archetype prompt)
```

## Common Mistakes

- `autoApprove` is not a valid field — use `allowedTools` for auto-approve
- Empty arrays (`deniedCommands: []`) — omit entirely
- `toolsSettings` with alias keys (`shell:` instead of `execute_bash:`) — silently ignored
- Hooks in base crew.yaml with `crews/` directory — only `agentSpawn` deploys to generated agents
- Duplicate keyboard shortcuts — both get disabled
