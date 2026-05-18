# Workspace

Every deployed project has a **workspace contract**: two project-scoped roots where
agents leave artifacts. The contract is intentionally minimal — two paths and one
rule about lifecycle.

## Shape

```yaml
# .crews/crew.yaml
workspace:
  ephemeral: .scratch
  durable: .memory
```

The block is optional. Omit it and the product defaults `.scratch` + `.memory`
apply. **If `workspace:` is present, both `ephemeral:` and `durable:` are required**
— partial overrides are rejected at build time. There is no `null`/disable; either
override both roots or take both defaults.

## Roots

| Root | Default | Lifecycle | Use for |
|------|---------|-----------|---------|
| Ephemeral | `.scratch` | ≤ one handoff cycle | Current handoff, scratch notes, draft artifacts |
| Durable | `.memory` | Survives across sessions; promotion is explicit | Curated decisions, distilled findings, references worth keeping |

Promotion from ephemeral to durable is intentional. Never link to ephemeral content
from durable docs; treat the ephemeral root as expendable.

## What the build does

For every project (`build_single_project` and the legacy `_sync_project_crews`
path):

1. Pre-creates `<project>/<ephemeral>/` and `<project>/<durable>/`.
2. Emits `.kiro/steering/universal/workspace.md` describing both roots, their
   lifecycle, and where the standardized handoff lives. This is always-loaded
   steering, so every agent sees the resolved paths.
3. Substitutes `{{workspace.ephemeral}}` and `{{workspace.durable}}` in every
   synced prompt under `shared/prompts/` so the configured roots flow into
   `@handoff`, `@read-handoff`, and any future workspace-aware prompts.

The generator owns **topology** (directories + the canonical steering file) and
nothing else. It never authors content inside the workspace roots and never invents
durable artifact taxonomy — that is each project's call.

## Handoff convention

The standardized handoff artifact (ADR 0013) lives at
`<ephemeral>/HANDOFF.md`. `@handoff` writes it, `@read-handoff` reads it, and a
newer handoff with the same `handoff_key` supersedes the older one. The shared
template at `shared/templates/handoff.md` defines the canonical frontmatter +
five required sections (`Objective`, `Constraints`, `Prior Decisions`,
`Current State`, `Next Steps`) plus an optional `Evidence` block.

## Frontmatter rule

Any artifact another agent or future session may read — anything in the workspace
roots — MUST carry the standard YAML header:

```yaml
---
created_at: <ISO 8601 with offset>
base_commit: <git rev-parse --short HEAD at creation>
---
```

Handoffs additionally include `handoff_key`. Private scratch that only you will
read is exempt.

## Why a closed contract

Consistent with ADR 0012 (config simplicity): the public surface is two paths and
one supersession rule. Anything richer (durable artifact taxonomy, lifecycle
policies, retention windows) lives in skills or per-project conventions, not in
the public config. If those grow, we revisit the contract — until then, this is
the whole API.
