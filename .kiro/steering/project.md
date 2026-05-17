---
inclusion: always
---

# agent-crews — Project Context

## What This Is
A repo for creating, maintaining, and improving agent teams for kiro-cli coding projects. Contains the base crew template, component system, generation tooling, and analysis scripts.

## Layout
```
base/              # Base template (crews/*.yaml — generic names)
shared/            # Shared resources (components, themes, skills, steering)
projects/          # Per-project adaptations (crew.yaml + generated agents)
docs/              # Specs, decisions, guides
.crews/crew.yaml         # Project registry + component defaults + theme config
generate.py        # crews/*.yaml + components + theme → .kiro/agents/*.json + steering
analyze-session.py # Session transcript analysis
.kiro/             # This repo's own agents, skills, prompts
```

## Workflow
1. Create/edit crew YAML in `base/crews/`
2. Configure project in `.crews/crew.yaml`
3. Generate: `just build .`
4. Test in target project: `just build <project>`
5. Iterate: edit crew/component, regenerate

## Key Commands
- `just build .` — generate this repo's agents
- `just build <project>` — generate a specific project
- `just build --all` — generate all projects
- `just status` — show fleet deployment status
- `just check` — validate health
- `just eval` — run behavioral evals

## Post-Change Rule
After ANY modification to crew.yaml, crews/*.yaml, or shared/components/, ALWAYS run `just build` before considering the task complete. Generation is not optional — it's part of the change.

## Conventions
- crew.yaml + crews/*.yaml are the source of truth (never edit generated .json files)
- Shared skills live in `shared/skills/`, project-specific in `<project>/.kiro/skills/`
- Behavioral rules live in `shared/components/` (never inline in crew prompts)
- Conventional commits: feat/fix/docs(scope): description
- All generation happens here, target projects get pre-built artifacts

## Git Discipline
- After completing any task, ALWAYS commit and push the changes
- Use conventional commits: feat/fix/docs/chore(scope): description
- Stage specific files (not `git add .`) to avoid committing unrelated changes
- Push immediately after commit — do not defer
- If multiple logical changes, make multiple commits (one per concern)