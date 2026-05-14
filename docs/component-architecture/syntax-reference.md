# Component Architecture — Syntax Reference

Quick lookup for all configuration formats. Start with the summary, drill into sections as needed.

---

## At a Glance

| Format | File | When You Need It |
|---|---|---|
| [Component declaration](#component-declaration) | `shared/components/<name>/<variant>.yaml` | Creating or editing a component |
| [Project config](#project-component-configuration) | `projects/<name>/.kiro/crew.yaml` | Configuring components for a project |
| [Theme spec](#theme-specification) | `projects/<name>/.kiro/theme.yaml` | Defining a project's voice/personality |
| [Fleet config](#fleet-configuration) | `fleet.yaml` + `fleet.local.yaml` | Managing project inventory |
| [Agent JSON](#kiro-cli-agent-json) | `.kiro/agents/<name>.json` | Understanding generated output |
| [Custom subagent](#kiro-cli-custom-subagent) | `.kiro/agents/<name>.md` | Defining a subagent (verifier, editor) |
| [Steering file](#kiro-cli-steering-files) | `.kiro/steering/*.md` | Behavioral rules for all agents |
| [Skill file](#kiro-cli-skills) | `.kiro/skills/<name>/SKILL.md` | On-demand knowledge |
| [Hooks](#kiro-cli-hooks) | Inside agent JSON | Auto-triggered commands |
| [Placeholders](#placeholder-substitution) | Inside component YAML | Template values from project config |
| [Subagent behavior](#kiro-cli-subagent-behavior) | (reference) | What subagents inherit vs don't |
| [CLI commands](#kiro-cli-commands) | (reference) | Common kiro-cli commands |

---

## Component Declaration

`shared/components/<component-name>/<variant>.yaml`

```yaml
name: <component>-<variant>
description: "<one-line>"
targets: [worker]                    # worker | orchestrator | all
prompt: |
  ## <Section Title>
  <injected into agent prompt>
allowed_commands:                    # → execute_bash.allowedCommands
  - "git *"
resources:                           # → agent resources array
  - "skill://.kiro/skills/<name>.md"
hooks:                               # → agent hooks
  postToolUse:
    - matcher: "fs_write"
      command: "<command>"
steering: |                          # → written as .kiro/steering/<component>.md
  ---
  inclusion: always
  ---
  # <Title>
  <inherited by subagents>
subagents:                           # → generates additional agent .json/.md files
  - name: <name>
    description: "<desc>"
    tools: ["read"]
    prompt: |
      <subagent prompt>
```

**Fields:** `targets` determines injection. `prompt` goes into agent prompt. `allowed_commands` merges into shell whitelist. `steering` ensures subagent inheritance. `subagents` generates verifier/editor definitions.

---

## Project Component Configuration

`projects/<name>/.kiro/crew.yaml` — `components:` section

```yaml
components:
  signaling: standard                    # simple: variant name
  narration: verified                    # simple: variant name
  git:
    workflow: checkpoint                  # variant + config
    worktrees: false
  search:
    sources: [local, cached-docs, web]   # compositional
    priority: "cached → local → web"
    conflict: first-authoritative
  notifications:
    channels: [toast]
    policy: completions
  verification:
    checks:
      build: "cargo check"
      test: "cargo test"
      lint: "cargo clippy"
    skip_types: []
    explicit_types: {}
  troubleshooting:
    methodology: systematic
    escalation:
      same_approach: 2
      strategies: 3
      action: ask-user
  writing:
    style: standard
    editor:
      triggers: [new-document, significant-revision, user-facing]
    theme: null
  completion:
    handoff: standard                    # preset OR custom include list
    followups: file-issues
```

**Patterns:** String = load variant directly. Map = variant + overrides. `{{placeholders}}` in components are substituted from these values.

---

## Theme Specification

`projects/<name>/.kiro/theme.yaml`

```yaml
name: nautical
domain: "Age of sail, exploration, maritime navigation"
vocabulary:
  use: [chart, navigate, sail, anchor, reef, horizon]
  avoid: [drive, road, highway]
tone: "Confident but not pirate-campy. Professional sailor, not Jack Sparrow."
examples:
  - "Charting a course through the auth module. Two reefs spotted."
  - "Anchoring this branch — all tests pass, ready for port."
anti-examples:
  - "Arr matey! Shiver me timbers!"
  - "Navigating the ever-evolving landscape of..."
```

**Required:** name, domain, vocabulary (use + avoid), tone, 3+ examples, 2+ anti-examples. Applies to narration/notifications only — committed artifacts use standard style.

---

## Fleet Configuration

```yaml
# fleet.yaml (committed)
defaults:
  persona: personal
  components: { ... }

projects:
  ferris-tracker:
    type: custom
    theme: nautical
```

```yaml
# fleet.local.yaml (gitignored)
deployments:
  ferris-tracker: C:\Users\dev\code\ferris-tracker
```

**Split:** `fleet.yaml` = what exists (shared). `fleet.local.yaml` = what's deployed here (per-machine).

---

## Kiro CLI Agent JSON

`.kiro/agents/<name>.json` — **generated, never edit directly**

```json
{
  "name": "agent-name",
  "description": "What this agent does",
  "prompt": "Inline text OR file://./path.md",
  "model": "claude-sonnet-4",
  "keyboardShortcut": "ctrl+shift+a",
  "welcomeMessage": "Greeting on switch",
  "includeMcpJson": true,
  "tools": ["read", "write", "shell", "subagent", "@mcp-server", "*"],
  "allowedTools": ["read", "@git/git_status", "@server/read_*"],
  "toolAliases": { "@github-mcp/get_issues": "github_issues" },
  "toolsSettings": {
    "subagent": { "availableAgents": [...], "trustedAgents": [...] },
    "execute_bash": { "allowedCommands": [...], "deniedCommands": [...], "autoAllowReadonly": true },
    "fs_write": { "allowedPaths": ["./**"] }
  },
  "resources": ["file://...", "skill://...", { "type": "knowledgeBase", ... }],
  "hooks": { "agentSpawn": [...], "preToolUse": [...], "postToolUse": [...], "stop": [...] }
}
```

**Key distinctions:** `tools` = what CAN be used. `allowedTools` = what runs without confirmation. `resources` with `file://` = always loaded. `skill://` = on-demand.

---

## Kiro CLI Custom Subagent

`.kiro/agents/<name>.md`

```markdown
---
name: code-reviewer
description: Expert code review assistant
tools: ["read", "@context7"]
model: claude-sonnet-4
---

You are a senior code reviewer.
```

**Frontmatter:** `name` (required), `description`, `tools`, `model`, `includeMcpJson`, `includePowers`. Body = the prompt.

**Invocation:** Automatic (kiro matches by description), explicit ("Use the code-reviewer subagent"), or slash (`/code-reviewer <task>`).

---

## Kiro CLI Steering Files

`.kiro/steering/*.md`

```markdown
---
inclusion: always
---

# Title

Rules loaded into ALL agents including subagents.
```

**Key property:** Inherited by subagents automatically. This is how behavioral rules propagate to workers without explicit passing.

---

## Kiro CLI Skills

`.kiro/skills/<name>/SKILL.md`

```markdown
---
name: writing-style
description: "Use when writing or reviewing prose, docs, comments."
---

# Writing Style

Full content loaded on demand.
```

**Key property:** Only metadata loaded at startup. Full content loaded when agent determines it's relevant. Description must be specific for reliable matching.

---

## Kiro CLI Hooks

```json
{ "matcher": "fs_write", "command": "cargo fmt --all" }
```

| Trigger | When | Blocks? |
|---|---|---|
| `agentSpawn` | Agent activated | No |
| `userPromptSubmit` | User sends message | No |
| `preToolUse` | Before tool runs | Yes |
| `postToolUse` | After tool runs | No |
| `stop` | Assistant done responding | No |

**Internal tool names:** `fs_read`, `fs_write`, `execute_bash`, `use_aws`. Hooks do NOT fire in subagents.

---

## Kiro CLI Subagent Behavior

| Property | Main Agent | Subagent |
|---|---|---|
| Conversation history | Full | Fresh (empty) |
| Steering files | ✅ | ✅ (same) |
| MCP servers | ✅ | ✅ (same) |
| Skills | ✅ | ✅ |
| Hooks | ✅ | ❌ |
| Specs | ✅ | ❌ |
| Peer awareness | N/A | ❌ |
| Max parallel | N/A | ~4 |

---

## Kiro CLI Commands

| Command | Purpose |
|---|---|
| `/agent <name>` | Switch to agent |
| `/agent swap` | Switch to previous |
| `/<skill-name>` | Invoke skill |
| `/model` | Show/change model |
| `/plan` / `Shift+Tab` | Plan agent |
| `/chat resume` | Resume session |
| `ctrl+g` | Subagent status |

---

## Placeholder Substitution

Components use `{{key}}` — substituted from project's `components:` config at generation time.

| Placeholder | Source |
|---|---|
| `{{checks.build}}` | `components.verification.checks.build` |
| `{{checks.test}}` | `components.verification.checks.test` |
| `{{checks.lint}}` | `components.verification.checks.lint` |
| `{{escalation.same_approach}}` | `components.troubleshooting.escalation.same_approach` |
| `{{escalation.strategies}}` | `components.troubleshooting.escalation.strategies` |
| `{{escalation.action}}` | `components.troubleshooting.escalation.action` |
| `{{sources}}` | `components.search.sources` |
| `{{priority}}` | `components.search.priority` |
| `{{conflict}}` | `components.search.conflict` |
| `{{channels}}` | `components.notifications.channels` |
| `{{policy}}` | `components.notifications.policy` |
| `{{theme_note}}` | From theme.yaml or "No theme configured." |
