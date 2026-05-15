# ADR-007: .crews/ Directory Separation

**Status:** Implemented  
**Date:** 2026-05-15

## Context

agent-crews generates and deploys AI agent configurations to target projects. Currently, everything lands in `.kiro/` — both kiro-native files (agents, prompts, steering) and agent-crews machinery (crew definitions, evals, metadata, scripts).

This creates three problems:

1. **Unclear ownership.** Users can't tell which files are consumed by kiro-cli vs which are agent-crews plumbing.
2. **Portability friction.** Crew source files are mixed with generated output. Can't rehydrate without knowing which files are which.
3. **Eval and crew config belong to the project.** They should be committable and usable independently — anyone with agent-crews can regenerate from them.

## Decision

Separate agent-crews files into `.crews/` at the project root. `.kiro/` contains only kiro-native configuration.

```
~/code/my-project/
  .kiro/                    ← kiro-native (generated output)
    agents/*.json
    prompts/*.md
    steering/**/*.md
    skills/
  .crews/                   ← agent-crews machinery (source of truth)
    crew.yaml               ← project config (self-contained, no inheritance)
    evals.yaml              ← behavioral smoke tests
    scripts/                ← notification/validation scripts
    overrides/              ← (optional) project-specific agent overrides
```

## Key Design Decisions

1. **`.crews/crew.yaml` is fully self-contained.** No inheritance from shared defaults. Defaults are applied at creation time only.
2. **fleet.yaml eliminated.** `fleet.local.yaml` is the sole project registry (name→path mapping, auto-maintained by scanner).
3. **Project's `.crews/` is authoritative.** `just build foo` reads directly from `~/code/foo/.crews/` and writes `~/code/foo/.kiro/`. No intermediate staging for normal workflow.
4. **Staging is temporary.** `projects/` directory in agent-crews is for first-gen and testing only. After push to project, staging is deleted.
5. **Copy as default deploy.** Enables committing `.kiro/` in target. Symlink available as opt-in for dev iteration.
6. **Base crews referenced by name.** `.crews/crew.yaml` says `crews: [general, bug-fix]`. Full definitions resolved from agent-crews `base/crews/` at build time. No stale forks.
7. **agent-crews is just another project.** Listed in fleet.local.yaml, same build flow as any project.
8. **`AGENT_CREWS_HOME` env var** enables cross-project invocation (`just build .` from any project).
9. **Breaking change + migration script.** No dual-layout support.

## Alternatives Considered

- **Keep everything in `.kiro/`.** Status quo. Rejected — mixes source and output.
- **Use `.kiro/crews/` subdirectory.** Rejected — still inside `.kiro/`, unclear ownership, kiro-cli might claim that namespace.
- **Dual-layout transition period.** Rejected — only 3 projects to migrate, complexity not justified.
- **Full crew YAML copies in `.crews/crews/`.** Rejected — creates stale forks that miss upstream improvements.

## Consequences

- `generate.py` reads `.crews/crew.yaml` from target project, writes `.kiro/` output directly
- `fleet.local.yaml` becomes the sole registry (scanner-maintained)
- Eval runner discovers `.crews/evals.yaml` in cwd
- Projects can commit `.crews/` (source) and optionally `.kiro/` (output) — user's choice
- Migration script moves existing files from `.kiro/` to `.crews/`
- `bin/agent-crews` wrapper + `AGENT_CREWS_HOME` enables use from any directory
