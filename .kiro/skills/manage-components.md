---
name: manage-components
description: Process for creating, modifying, and debugging behavioral components. Use when adding a new component, editing component behavior, or troubleshooting component delivery.
---

# Manage Components Process

## Component structure

Components live in `shared/components/<name>/`. Each variant is a YAML file:

```
shared/components/
  verification/
    gate.yaml          # variant: gate
  git/
    checkpoint.yaml    # variant: checkpoint
    pr-based.yaml      # variant: pr-based
    manual.yaml        # variant: manual
```

## Component YAML format

```yaml
name: component-variant
description: "What this component does"

targets: [worker]          # worker, orchestrator, or universal

prompt: ""                 # injected into agent prompt (rarely used)

allowed_commands:          # shell commands agents can run
  - "{{checks.build}}"    # template vars from fleet.yaml

resources: []              # additional resource files
hooks: {}                  # lifecycle hooks

steering: |                # the behavioral rules (delivered as steering file)
  ---
  inclusion: always
  ---
  # Protocol Name
  
  Rules go here...

subagents: []              # subagent definitions (e.g., verifier, editor)
```

## Creating a new component

### Step 1: Identify the concern

A component should be:
- Cross-cutting (applies to multiple agents/projects)
- Behavioral (defines HOW agents work, not WHAT they build)
- Configurable (variants or template variables for per-project tuning)

### Step 2: Choose target

- `worker` — specialists (builder, tester, researcher)
- `orchestrator` — leads (general-lead, bugfix-lead)
- `universal` — all agents

### Step 3: Write the YAML

Create `shared/components/<name>/<variant>.yaml`:

```yaml
name: <name>-<variant>
description: "Brief description"
targets: [worker]
prompt: ""
allowed_commands: []
resources: []
hooks: {}
steering: |
  ---
  inclusion: always
  ---
  # Protocol Name
  
  ## Rules
  - Rule 1
  - Rule 2
subagents: []
```

### Step 4: Wire into fleet.yaml defaults

Add to `fleet.example.yaml` under `defaults.components`:

```yaml
defaults:
  components:
    your_component:
      variant: your-variant
      # any config keys agents need
```

### Step 5: Regenerate and verify

```bash
just build
```

Check that the steering file appears in `.kiro/steering/<target>/`:
```bash
cat .kiro/steering/worker/your-component.md
```

## Modifying an existing component

1. Edit the YAML in `shared/components/<name>/<variant>.yaml`
2. Run `just build`
3. Verify the steering output in `.kiro/steering/`
4. Run evals if the component has coverage: `just eval-components`

## Template variables

Components can reference fleet.yaml config via `{{variable}}`:

```yaml
steering: |
  - Build: `{{checks.build}}`
  - Test: `{{checks.test}}`
```

These are resolved at generation time from the project's component config.

## Delivery path

Generator reads component YAML → writes steering to:
- `targets: [worker]` → `.kiro/steering/worker/<name>.md`
- `targets: [orchestrator]` → `.kiro/steering/orchestrator/<name>.md`
- `targets: [universal]` → `.kiro/steering/universal/<name>.md`

Agents load steering via resource globs — no manual wiring needed.

## Debugging

If a component isn't taking effect:
1. Check `fleet.yaml` — is the component configured for this project?
2. Check `just build` output — any errors?
3. Check `.kiro/steering/<target>/` — is the file present?
4. Check the agent's `resources` field — does it glob the right steering directory?
