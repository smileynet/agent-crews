# Components

Components are reusable behavioral rules that apply across all agents in a crew. Change a component once, regenerate, and every agent picks up the new behavior.

## What components do

Instead of copy-pasting instructions into every agent prompt, components deliver behavioral rules via steering files. Agents inherit them automatically based on their role (orchestrator vs worker).

## Available components

| Component | What it controls |
|-----------|-----------------|
| verification | How agents verify their work (build, test, lint commands) |
| git | Commit style, push behavior, branch strategy |
| troubleshooting | Root-cause investigation, escalation rules |
| search | Where agents look for information and in what order |
| memory | What agents remember across sessions |
| notifications | When and how agents notify you of completion |
| task_tracking | How agents track multi-step work |
| decisions | When to log decisions vs write ADRs |
| handoff | When to suggest switching to a different crew |
| narration | How agents report progress and verify claims |
| writing | Style rules, editor triggers, theme voice |
| completion | What agents do when finishing (signal, push, notify) |
| sanity_gate | Assumption tracking, rubber-stamp prevention |

## Configuring components

Set defaults in `fleet.yaml` under `defaults.components`, override per-project:

```yaml
defaults:
  components:
    verification:
      checks:
        build: null
        test: null
        lint: null
    git:
      variant: checkpoint

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

## How they're delivered

Components generate steering files into `.kiro/steering/`:

```
.kiro/steering/
  universal/       # Rules for ALL agents (sanity, completion, signaling)
  orchestrator/    # Rules for leads (task tracking, decisions, narration)
  worker/          # Rules for specialists (verification, git, troubleshooting)
```

Agents load these via resource globs — orchestrators get orchestrator + universal, workers get worker + universal.

## Creating new components

See the [component architecture spec](component-architecture/spec.md) for the full design. New components go in `shared/components/` and are wired through the generator.
