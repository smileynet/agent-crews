# Contributing to agent-crews

Contributions welcome — crews, components, skills, themes, docs, and bug fixes.

## First Contribution

The fastest way to contribute:

1. Fork the repo
2. Pick a [`good-first-issue`](../../labels/good-first-issue) or fix a typo in docs
3. Follow the setup below
4. Open a PR

## Setup

```bash
# Prerequisites: uv (required), mise (optional)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure
cp fleet.example.yaml fleet.yaml

# Build + verify
just build
```

## Development Workflow

```
Edit source (crews, components, skills, themes)
  → just build (regenerate)
  → just check (validate)
  → commit + PR
```

The source of truth is always YAML — never edit generated `.json` files.

## What You Can Contribute

| Type | Location | Guide |
|------|----------|-------|
| Crew | `base/crews/{name}.yaml` | [Adding a crew](#adding-a-crew) |
| Component | `shared/components/{name}/` | [Adding a component](#adding-a-component) |
| Skill | `shared/skills/{name}.md` | [Adding a skill](#adding-a-skill) |
| Theme | `shared/themes/{name}.yaml` | [Adding a theme](#adding-a-theme) |
| Eval | `tests/crew-evals.yaml` | [Adding an eval](#adding-an-eval) |

## Adding a Crew

1. Create `base/crews/{name}.yaml` following existing crew structure
2. Define: `workflow`, `scope` (handles/refuses), `architypes` (orchestrator + workers)
3. Each agent needs: `name`, `description`, `routes`, `prompt`
4. Run `just build` — verify generation succeeds
5. Add theme mappings to `shared/themes/*.yaml` if applicable

## Adding a Component

1. Create `shared/components/{name}/` directory
2. Add variant YAML files (e.g., `standard.yaml`, `strict.yaml`)
3. Each variant defines: steering text, `allowed_commands`, `target` (all/orchestrator/worker)
4. Register in `fleet.example.yaml` defaults
5. Run `just build` — verify steering generation

## Adding a Skill

1. Create `shared/skills/{name}.md` (single-file) or `shared/skills/{name}/SKILL.md` (multi-file)
2. Add YAML frontmatter with `name` and `description`
3. Description is the trigger — be specific about when it should load
4. Keep the main skill under 100 lines

### Multi-File Skills (lazy linking)

When a skill has domain-specific variants or reference material:

```
shared/skills/my-skill/
├── SKILL.md              # Core skill (loaded on trigger, ≤100 lines)
└── references/           # Read on demand by agent
    ├── examples-typescript.md
    ├── examples-rust.md
    └── checklist.md
```

**How it works:** Only `SKILL.md` loads into context on trigger. Reference files stay on disk. The skill's instructions tell the agent to `read` the relevant reference file when needed.

**Pattern in SKILL.md:**
```markdown
## Deployment steps
1. Check prerequisites in `references/checklist.md`
2. For ECS deployments, follow `references/ecs-guide.md`
```

**Key principle:** SKILL.md = process steps (what to DO). References = context (what to KNOW).

**When to use multi-file:**
- Skill content diverges by language/framework/domain
- Reference tables exceed 20 lines
- Examples are stack-specific (not universally applicable)

**When to stay single-file:**
- Skill is universal (applies regardless of stack)
- Under 100 lines total
- No domain-specific variants

## Adding a Theme

1. Create `shared/themes/{name}.yaml`
2. Map generic agent names → themed names
3. Optionally add: icon, display name, welcome messages
4. Test: set `theme: {name}` on a project in fleet.yaml, run `just build`

## Adding an Eval

Add to `tests/crew-evals.yaml`:

```yaml
- name: my-new-eval
  agent: agent-name
  input: "The prompt to send"
  criteria: |
    What correct behavior looks like.
    What the agent should NOT do.
  tags: [routing]
  threshold: 4
```

Run with `just eval`.

## Conventions

- Conventional commits: `feat/fix/docs/chore(scope): description`
- `just build` after any change to crews, components, skills, or steering
- Keep steering files under 50 lines, skills under 100 lines
- Agent prompts: workflows over prose, tables over paragraphs

## Project Structure

```
base/crews/           Crew definitions (source of truth)
shared/components/    Behavioral concerns (steering templates)
shared/themes/        Cosmetic overlays
shared/skills/        On-demand knowledge
shared/steering/      Always-on steering (universal + per-persona)
generate.py           Generator (crews + components → .kiro/)
fleet.example.yaml    Reference config (committed)
fleet.yaml            Your config (gitignored)
```

## Changelog

Every user-facing change requires a changelog entry in `CHANGELOG.md` under `[Unreleased]`.

### What's user-facing?

If the change affects what someone deploying agent-crews can do, how they do it, or fixes something broken for them — it's user-facing. If you can't write the entry without naming a file, class, or internal module, it's probably not user-facing.

**Include:** New crews, components, themes, generator features, breaking changes, bug fixes.
**Exclude:** Refactors, test additions, internal tooling, steering tweaks, research artifacts.

### Entry format

Use [Keep a Changelog](https://keepachangelog.com/) categories: Added, Changed, Deprecated, Removed, Fixed, Security.

Write from the user's perspective:
- ✅ "Projects can now inherit base crews with `extends:` and override specific agents"
- ❌ "Added resolve_extends function to generate.py"

### When to write it

In the same commit as the change. You have the most context right now.

## Archetype Types

When creating or modifying crews, use the correct archetype type:

| Type | Depth | Can delegate to | Use for |
|------|:-----:|-----------------|--------|
| `dispatcher` | 0 | Orchestrators only | Project-level routing |
| `orchestrator` | 1 | Workers only | Crew leads |
| `worker` | 2 | Nobody | Task execution |

**Build-time enforcement:** `generate.py` validates these rules. A worker with `subagent` or an orchestrator targeting another orchestrator will fail the build.

Most crews only need `orchestrator` + `worker`. The `dispatcher` type is for project-level entry points that route across multiple crews.
