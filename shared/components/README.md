# Component System

Behavioral building blocks for agent crews. Each component is a YAML file that declares behavioral rules, tool permissions, and optional subagents.

## How It Works

```
.crews/crew.yaml defaults → project crew.yaml overrides → shared/components/<name>/<variant>.yaml
```

1. `.crews/crew.yaml` declares which component variant each project uses
2. `generate.py --all` loads components, substitutes project-specific config (`{{checks.build}}` etc.)
3. Generator writes steering files to `.kiro/steering/{universal,orchestrator,worker}/`
4. Agents load steering via resource globs — no prompt bloat, subagents inherit automatically

## Directory Structure

```
shared/components/
├── signaling/          standard, minimal, tracked
├── sanity-gate/        assumption-register
├── narration/          verified, evidence, self-report
├── troubleshooting/    systematic
├── verification/       gate
├── completion/         standard, minimal, full
├── git/                checkpoint, pr-based, manual
├── writing/            standard
├── handoff/            scope-based
├── decisions/          progressive, upfront, minimal
├── task-tracking/      soft-hard
├── search/             layered
├── memory/             four-tier
├── notifications/      channels
└── relay-protocol/     standard
```

## Component File Format

```yaml
name: <component>-<variant>
description: "<one-line>"
targets: [worker]              # worker | orchestrator | all
prompt: ""                     # empty for steering-only
allowed_commands: []           # merged into execute_bash.allowedCommands
resources: []                  # merged into agent resources
hooks: {}                      # merged into agent hooks
steering: |                    # written to .kiro/steering/{target}/<component>.md
  ---
  inclusion: always
  ---
  # <Title>
  <behavioral rules>
subagents: []                  # generates additional agent .json files
```

## Targets

| Target | Steering written to | Loaded by |
|--------|-------------------|-----------|
| `all` | `.kiro/steering/universal/` | All agents |
| `orchestrator` | `.kiro/steering/orchestrator/` | Orchestrators only |
| `worker` | `.kiro/steering/worker/` | Workers only |

Verifier and editor subagents intentionally get NO steering (fresh context for unbiased judgment).

## Adding a New Component

1. Create `shared/components/<name>/<variant>.yaml`
2. Add to `.crews/crew.yaml` defaults (and/or project overrides)
3. Run `just build`

## Overriding Per-Project

In `.crews/crew.yaml` under the project:

```yaml
projects:
  my-project:
    components:
      verification:
        checks:
          build: "cargo check"
          test: "cargo test"
          lint: "cargo clippy"
      git:
        variant: pr-based
```

## Placeholder Substitution

Use `{{key.subkey}}` in steering or allowed_commands. The generator resolves from the merged config:

- `{{checks.build}}` → project's build command
- `{{search.sources}}` → project's search source list
- `{{notifications.channels}}` → configured notification channels

## Scripts

Components can ship executable scripts that get deployed to `.kiro/scripts/` in target projects.

### Declaring scripts in a component

```yaml
# shared/components/notifications/channels.yaml
scripts:
  - file: notify-toast.sh
    description: "OS-native toast notification"
    args: "TITLE MESSAGE"
```

Script files live alongside the component YAML. The generator:
1. Copies scripts to `.kiro/scripts/` in the target project
2. Auto-adds them to `allowedCommands`
3. Generates `.kiro/steering/universal/scripts.md` listing all available scripts

### Config via mise

Scripts read config from environment variables, injected by mise:

```toml
# .mise.local.toml (gitignored)
[env]
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."
```

### Project-specific scripts

Declare in the project's crew.yaml:

```yaml
scripts:
  - file: scripts/run-godot-tests.sh
    description: "Run Godot test suite"
    args: "[SCENE_PATH]"
```
