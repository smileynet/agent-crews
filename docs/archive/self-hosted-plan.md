# Spec: Self-Hosted Plan

**Status:** Planned  
**Date:** 2026-05-13

## Goal

agent-crews eats its own dogfood. The system that generates `.kiro/` agents for other projects generates its own agents too. Personal project data is fully separated from the published open-source project.

## Current State

- `.kiro/agents/*.json` are hand-crafted, not generated
- `fleet.yaml` contains real personal projects (these are now gitignored)
- `projects/` contains real deployment outputs for those personal projects
- No `examples/` directory exists
- No meta crew definition — agent-crews has no crew YAML describing itself
- Docs mix user-facing and maintainer-facing content

## Target State

- `.kiro/` is generated from `base/crews/meta.yaml` via the same pipeline used for all projects
- `fleet.yaml` and `projects/` are gitignored — never published
- `fleet.example.yaml` provides reference material for users
- `examples/` generated from the working system as the final step
- Clear doc separation: user docs vs maintainer docs
- A project-hygiene agent validates the separation ongoing

## Ship Strategy

All phases execute on a single branch. Squash-merge when done.

One commit: `feat: self-host agent-crews crew generation + data separation`

No intermediate published states. This eliminates all chicken-and-egg concerns — every file referenced by any phase exists when the commit lands.

## Phases

| Phase | Name | Deliverable |
|-------|------|-------------|
| 2 | Meta Crew | `base/crews/meta.yaml` defining agent-crews' own crew |
| 3 | Fleet Wiring | agent-crews in fleet, `just build` generates .kiro/, idempotency proven |
| 1 | Data Separation | fleet.yaml/projects/ gitignored, fleet.example.yaml created |
| 4 | Doc Restructure | Clean user/maintainer doc split, CONTRIBUTING.md, AGENTS.md scrub |
| 5 | Hygiene Validation | project-hygiene agent validates all phases |
| FINAL | Generate Examples | `examples/` produced from the working system |

## Execution Order

Phase 2 first — meta crew is the foundation everything else builds on.  
Phase 3 next — proves generation works end-to-end.  
Phase 1 follows — data separation is safe because generation already works.  
Phase 4 — doc restructure reflects the generated state.  
Phase 5 — final validation pass.  
FINAL — generate `examples/` from the working system as the last action.

Sequence: 2 → 3 → 1 → 4 → 5 → generate examples/

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Option A: gitignore fleet.yaml and projects/ entirely | Clean separation. Users never see personal data. fleet.example.yaml shows the format. |
| 2 | Meta crew IS agent-crews' general crew | The "general crew always included" rule doesn't apply to agent-crews itself. Meta is purpose-built for this repo. |
| 3 | All phases ship together, single squash commit | No chicken-and-egg. No backward compat needed. fleet.example.yaml can reference `crews: [meta]` from the start. |
| 4 | New project-hygiene agent added to meta crew | Enforces data separation, doc accuracy, and sanitization ongoing. |
| 5 | Generated crews must be idempotent from configs | `just build` run twice with no config changes = zero diff. |
| 6 | Examples deferred to final step | examples/ generated from the working system after all phases complete. Not part of Phase 1. |
| 7 | Default persona is `personal`, not `sa` | `solutions-architect` is one example project persona, not the default. |

## Success Criteria

1. `git show HEAD:fleet.yaml` fails (file not in index)
2. `just build` generates `.kiro/agents/*.json` that match (or improve upon) current hand-crafted agents
3. `just build && just build && git diff --exit-code .kiro/` passes (idempotent)
4. `fleet.example.yaml` is valid, demonstrates the config format, contains no personal data
5. README references only published files — no broken links
6. project-hygiene agent passes all checks with zero findings
7. `examples/` contains instructive reference crews (generated as final step)
