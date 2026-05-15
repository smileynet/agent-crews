# AGENTS.md — agent-crews

Multi-agent crew builder for kiro-cli projects. Deploy specialized AI agent teams to any coding project.

## On Startup

If spawn hook reports issues, help the user fix them before proceeding.

- `uv` required — scripts use inline dependencies via `uv run`
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `winget install astral-sh.uv` (Windows)
- `mise` recommended — manages Python version and tools
  - Install: `curl https://mise.jdx.dev/install.sh | sh` (macOS/Linux) or `winget install jdx.mise` (Windows)
  - Then: `mise install` to get Python 3.12 + uv
- If both OK: ready to work. Show available agents and prompts.
- Fallback (no uv): `pip install pyyaml` then use `python generate.py` directly

## Design Principles

**High reliability** is the core value of agent-crews. Every decision favors correctness over speed.

- Enforcement over suggestion — tool permissions enforce; prompts suggest (ADR-001)
- Validation is automatic — augmenter → validator pipeline is the default
- Eval coverage required — behavioral changes need eval updates
- Changelog discipline enforced — user-facing changes require entries
- Generated output verified — `just build` must pass before done

See [ADR-006](docs/decisions/ADR-006-high-reliability.md) for full rationale.

## How this repo works

`base/crews/*.yaml` + `shared/components/*.yaml` are the source of truth. Never edit generated `.json` files directly.

```
base/              Base template
  crews/              Generic crew definitions (8 crews, 58 agents total)
    general.yaml      General purpose (12 agents)
    bug-fix.yaml      Bug fixing (8 agents)
    infrastructure.yaml  Infrastructure/deploy (7 agents)
    research.yaml     Research/docs (7 agents)
    onboarding.yaml   Brownfield onboarding (6 agents)
    hygiene.yaml      Project maintenance (6 agents)
    content.yaml      Presentations/tutorials (6 agents)
    writing.yaml      Writing/editing (6 agents)
shared/               Shared resources across all projects
  components/         Component system (14 behavioral concerns, 24 files)
  themes/             Theme overlays (cosmetic name/voice mapping)
  skills/             Shared skills
  steering/           Universal + persona-specific steering
projects/             Per-project adaptations
fleet.yaml            Project registry + component defaults + theme config
generate.py           crews/*.yaml + components + theme → .kiro/agents/*.json + steering
analyze-session.py    Session transcript analysis
.kiro/                This repo's own agents and prompts
```

## Crews (58 agents across 8 crews)

| Crew | Lead | Agents | Best For |
|------|------|:------:|----------|
| General | `/agent general-lead` | 12 | Mixed work, features |
| Bug Fix | `/agent bugfix-lead` | 8 | Bug fixing, testing |
| Infrastructure | `/agent infrastructure-lead` | 7 | Deploy, IaC |
| Research | `/agent research-lead` | 7 | Investigation, docs |
| Onboarding | `/agent onboarding-lead` | 6 | Brownfield repos |
| Hygiene | `/agent hygiene-lead` | 6 | Project maintenance |
| Content | `/agent content-lead` | 6 | Presentations, tutorials |
| Writing | `/agent writing-lead` | 6 | Writing, editing |

**Mandatory rule: general crew is ALWAYS included.** Every project gets the general crew as its baseline. Specialized crews (bug-fix, research, etc.) are added alongside general, never instead of it. A project with `crews: [research, writing]` is WRONG — it must be `crews: [general, research, writing]`.

### Theme Overlay (optional)

Themes rename agents cosmetically without changing behavior. Configure in fleet.yaml:
```yaml
projects:
  my-project:
    theme: wow  # general-lead → raid-leader, builder → paladin, etc.
```

See [Themed Crews Guide](docs/themed-crews-guide.md) for available themes and mappings.

## Common tasks

| Task | Command |
|------|---------|
| Generate all | `just build` |
| Generate one | `just generate <project>` |
| Generate components only | `just components` |
| Sync steering only | `just sync-steering` |
| Check health | `just check` |
| Deploy to project | `just link <project>` |
| Show fleet status | `just status` |
| Bootstrap all | `just bootstrap` |
| Validate schema | `just validate <project>` |
| Full CI | `just ci` |
| Smoke test (behavioral) | `just smoke-test <target-path>` |
| Integration test | `just integration-test <target-path>` |
| List sessions | `uv run analyze-session.py --project <name>` |
| Analyze session | `uv run analyze-session.py <id> --stats` |
| Ingest sessions (all tools) | `just ingest <project>` |
| Ingest all projects | `just ingest-all` |
| Project scan | `./scripts/project-scan.sh <path>` |
| Session summary | `./scripts/session-summary.sh <path>` |
| Crew health check | `./scripts/crew-health.sh <project>` |
| Cross-tool comparison | `uv run analyze-session.py --compare <path>` |
| Session diff (before/after) | `./scripts/session-diff.sh <path> <date>` |

## Post-Change Rule
After ANY modification to crew.yaml or crews/*.yaml, ALWAYS run `just build` before considering the task complete. Generation is not optional — it's part of the change.

## Deploy Checklist

Every project deployment MUST include a `@crew-sheet` prompt:
- Auto-generated at `projects/<project>/.kiro/prompts/crew-sheet.md` by `just build`
- Lists all crews, agents, roles, and common tasks
- Uses the project's actual agent names (themed if theme is active)

## Agents (for this repo)

| Agent | Shortcut | Purpose |
|-------|----------|---------|
| dispatcher | `ctrl+shift+d` | Orchestrator — routes to the correct agent based on intent |
| crew-researcher | `/agent crew-researcher` | Deep investigation — patterns, prior art, best practices |
| crew-creator | `ctrl+shift+c` | Build a crew for a new project |
| crew-doctor | `ctrl+shift+f` | Diagnose and fix crew issues |
| crew-augmenter | `/agent crew-augmenter` | Research + add new agents/features to existing crews |
| kiro-helper | (subagent) | Kiro CLI schema lookups — delegated to by other agents |
| crew-analyst | `/agent crew-analyst` | Analyze sessions, find protocol gaps, recommend crew improvements |
| project-hygiene | `/agent project-hygiene` | Data separation, doc accuracy, sanitization auditing |
| crew-validator | `/agent crew-validator` | Validate changes — build, changelog, structure, drift, eval coverage |
| crew-releaser | `/agent crew-releaser` | Release pipeline — changelog curation, version bump, tag, publish |

The `dispatcher` is the default entry point. It delegates to the specialist agents. Start with `/agent dispatcher` if unsure which agent to use.

## Prompts

| Prompt | Purpose |
|--------|---------|
| `@create-crew` | Guided project onboarding |
| `@review-crew-quality` | Audit crew against conventions (context budget, skills, configs) |
| `@review-session` | Analyze one session |
| `@review-crew` | Cross-session performance review |
| `@deploy-crew` | Regenerate and deploy |
| `@tune-crew` | Full tuning loop: analyze sessions → diagnose → fix → validate |
| `@release` | Cut a release — validate, curate changelog, bump version, tag |
| `@crew-sheet` | Show all agents, prompts, and common tasks |
| `@grill-me` | Design interrogation — relentless questioning until shared understanding |
| `@thunderdome` | Ruthless editing — every feature fights to earn its place |

## Doc index

| Doc | What it covers |
|-----|---------------|
| [docs/use-case-guide.md](docs/use-case-guide.md) | Common workflows — how to use deployed agents |
| [docs/themed-crews-guide.md](docs/themed-crews-guide.md) | Theme overlay — game-themed agent names and when to use each |
| [base/crews/](base/crews/) | Generic crew definitions (8 crews) |
| [shared/themes/](shared/themes/) | Theme overlays (cosmetic name mapping) |
| [shared/components/](shared/components/) | Component system (14 behavioral concerns) |
| [shared/skills/](shared/skills/) | Shared skills library |
| [fleet.yaml](fleet.yaml) | Project registry + component defaults + theme config |
| [docs/component-architecture/spec.md](docs/component-architecture/spec.md) | Component architecture specification |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records |
