---
name: manage-components
description: Guide users through creating and modifying behavioral components. Ask relevant questions, surface design considerations, prevent common mistakes.
---

# Components — Advisory Guide

## When a user wants to create a new component

Ask:
- What behavior are you trying to standardize? (e.g., "how agents handle errors")
- Does this apply to all agents, just leads, or just workers?
- Should it be configurable per-project, or one-size-fits-all?
- Does an existing component already cover this? (check `shared/components/`)

Key considerations to surface:
- Components are for cross-cutting concerns — if it only applies to one agent, it belongs in the agent prompt
- Keep components focused on ONE behavioral concern
- Template variables (`{{key}}`) let projects customize without forking the component
- Multiple variants (e.g., `checkpoint` vs `pr-based` for git) are better than one complex component with many conditionals

## When a user wants to modify a component

Ask:
- Which component and variant? (`shared/components/<name>/<variant>.yaml`)
- Is this a universal change or should it be a new variant?
- Will this affect all projects using this component?

Key considerations to surface:
- Changes propagate to ALL projects on next `just build`
- If only one project needs different behavior, override in .crews/crew.yaml rather than changing the shared component
- Run evals after changes: `just eval-components`
- Check the generated steering to verify: `cat .kiro/steering/<target>/<name>.md`

## Component structure

Location: `shared/components/<name>/<variant>.yaml`

```yaml
name: component-variant
description: "What this does"
targets: [worker]           # worker | orchestrator | universal
steering: |
  ---
  inclusion: always
  ---
  # Protocol Name
  Rules here...
```

Targets determine delivery:
- `worker` → `.kiro/steering/worker/`
- `orchestrator` → `.kiro/steering/orchestrator/`
- `universal` → `.kiro/steering/universal/`

## When a component isn't working

Ask:
- Is the component configured in .crews/crew.yaml for this project?
- Did you run `just build` after changes?

Debug path:
1. Check .crews/crew.yaml config for the project
2. Check `just build` output for errors
3. Check `.kiro/steering/<target>/` for the generated file
4. Check agent's `resources` field includes the steering glob

## Common mistakes to prevent

- Don't put project-specific details in shared components (use template vars)
- Don't combine unrelated concerns in one component (split them)
- Don't write components that duplicate what's in agent prompts (components are for shared behavior, prompts are for identity)
- Don't forget to regenerate after changes (`just build`)
