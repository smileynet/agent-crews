# Spec: Phase 4 — Doc Restructure

**Status:** Planned  
**Date:** 2026-05-13  
**Depends on:** Phase 3 (AGENTS.md must reflect generated state)

## Objective

Clear separation between user-facing docs (how to use agent-crews) and maintainer-facing docs (how agent-crews works internally). Scrub stale references from AGENTS.md.

## Doc Classification

### User-Facing (published, for consumers)

| File | Purpose |
|------|---------|
| `README.md` | What this is, how to use it, quick start |
| `docs/use-case-guide.md` | When to use which crew |
| `docs/themed-crews-guide.md` | How themes work, available themes |
| `examples/` | Reference output — what generated crews look like (generated as final step) |
| `CONTRIBUTING.md` | **NEW** — how to add crews, components, themes |

### Maintainer-Facing (internal, for contributors)

| File | Purpose |
|------|---------|
| `AGENTS.md` | Current agent roster (reflects generated .kiro/) |
| `docs/component-architecture/` | Component system internals |
| `docs/decisions/` | ADRs — why things are the way they are |
| `docs/specs/` | Implementation specs (including this one) |

## README.md Updates

Restructure to focus on usage:

```markdown
# agent-crews

Multi-agent crew builder for Kiro projects.

## What It Does
[1-2 sentences: generates .kiro/ agents from crew definitions]

## Quick Start
1. Copy `fleet.example.yaml` → `fleet.yaml`
2. Add your projects
3. Run `just build`
4. Copy generated output to your project

## Configuration
[Reference fleet.example.yaml format, link to examples/]

## Available Crews
[Table: crew name, agent count, purpose — link to use-case-guide]

## Available Themes
[Brief list — link to themed-crews-guide]

## Examples
See `examples/` for complete generated output.

## Contributing
See CONTRIBUTING.md.
```

Remove from README:
- Internal architecture details (→ docs/component-architecture/)
- Decision rationale (→ docs/decisions/)
- Spec references (→ docs/specs/)
- Any personal project names

## AGENTS.md Scrub

This happens AFTER Phase 3 generation so it reflects actual output. Specific actions:

1. **Remove `sa-crew/crews/` references** — stale path, no longer exists
2. **Remove personal project names** from any examples (see validate.sh blocklist)
3. **Update agent roster** to match `.kiro/agents/*.json` exactly
4. **Update prompt list** to match `.kiro/prompts/*.md` exactly
5. **Reflect generated state** — AGENTS.md describes what the meta crew produces, not hand-crafted history

Update process:

1. Run `just build agent-crews`
2. List `.kiro/agents/*.json` — extract name + description
3. List `.kiro/prompts/*.md` — extract name + first line
4. Rewrite AGENTS.md to match

Can be automated as part of the build step.

## CONTRIBUTING.md (New)

Contents:

- **Adding a New Crew:** Create `base/crews/{name}.yaml`, follow existing structure, test with `just build`
- **Adding a Component:** Create `shared/components/{name}/`, add templates, register in loader
- **Adding a Theme:** Create `shared/themes/{name}.yaml`, map agent names, add voice settings
- **Running Locally:** `just build`, `just build {project}`, `python -m pytest tests/`
- **Project Structure:** Brief map of key directories

## Verification

- [ ] README.md contains no internal architecture details
- [ ] README.md references fleet.example.yaml (not fleet.yaml)
- [ ] README.md contains no personal project names
- [ ] CONTRIBUTING.md exists with crew/component/theme instructions
- [ ] AGENTS.md matches `.kiro/agents/*.json` exactly
- [ ] AGENTS.md contains no `sa-crew/crews/` references
- [ ] AGENTS.md contains no personal project names
- [ ] All internal links in all docs resolve
- [ ] User-facing docs make sense to someone who has never seen the codebase
