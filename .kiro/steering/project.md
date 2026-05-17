---
inclusion: always
---

# agent-crews — Project Context

## Scope Of This File

- Keep this file short. It is runtime context for deployed agents, not a design memo.
- Put facts here that most agents need on most turns. Put reusable crew behavior in source config, components, skills, or prompts instead.
- When a detail only matters for one task, pass it in the task or handoff instead of growing this file.

## Runtime Boundary

- `.kiro/` is this repo's instantiated crew: generated agents, prompts, skills, and local steering for working on `agent-crews`.
- `.crews/crew.yaml` selects which crews/components this repo deploys for itself.
- `base/`, `shared/`, `_lib/`, and `generate.py` define how crews are built and deployed to any project.
- Never hand-edit generated `.kiro/agents/*.json`; change source inputs, then rebuild.

## What This Project Is

A repo for creating, maintaining, and improving agent teams for kiro-cli coding projects. It contains reusable crew templates, composable behavior components, generation/deployment tooling, and self-hosted examples/tests.

## Layout
```
base/              # Source crew templates (generic capability definitions)
shared/            # Shared components, skills, prompts, steering, and themes
_lib/              # Build, sync, validation, and deployment logic
.crews/crew.yaml   # This repo's self-hosted crew selection and component config
.crews/evals.yaml  # Behavioral eval suite for this repo
.kiro/             # Generated runtime artifacts for this repo's deployed crew
examples/          # Example deployed projects and generated outputs
docs/              # Specs, ADRs, proposals, and guides
generate.py        # CLI entry point for build/sync/check operations
justfile           # Standard commands for build, test, eval, release prep
```

## Workflow
1. Change source-of-truth inputs (`base/`, `shared/`, `_lib/`, `.crews/crew.yaml`, docs/tests as needed)
2. Regenerate affected deployments with `just build .` or `just build --all`
3. Verify behavior with focused tests, then broader gates when warranted
4. Update `CHANGELOG.md` for user-facing changes

## Key Commands
- `just build .` — regenerate this repo's deployed crew
- `just build --all` — regenerate this repo plus example outputs
- `just test` — run unit + e2e tests
- `just eval` — run the behavioral eval suite
- `just check .` — validate deployment health for this project

## Conventions
- Source of truth is YAML/code under `.crews/`, `base/`, `shared/`, and `_lib/`; generated `.kiro/` output is derived
- Shared skills live in `shared/skills/`; deployed copies live in `<project>/.kiro/skills/`
- Behavioral rules should live in components/skills/prompts, not ad hoc crew prompt prose
- Keep project context factual and sparse; avoid repeating generic agent-crews mechanics here

## DO NOT

- Do not edit generated `.kiro/agents/*.json` or treat `.kiro/` output as authoritative
- Do not add repo-specific build mechanics to shared project context unless every deployed project needs them
- Do not skip `just build` after changing deployed crew definitions or generation logic

## Key References

- `AGENTS.md` — repo operating rules and command guide
- `docs/proposals/deployment-gaps.md` — deployment pipeline gap tracking
- `docs/specs/project-context-in-fleet-config.md` — project context intent and boundaries
- `.kiro/prompts/crew-sheet.md` — actual deployed roster for this repo