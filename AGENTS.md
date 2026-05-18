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

## Runtime Boundary

- `.kiro/` is this repo's instantiated crew — generated agents, prompts, skills, and local steering. Treat it as build output.
- `.crews/crew.yaml` selects which crews this repo deploys for itself.
- `base/`, `shared/`, `_lib/`, and `generate.py` define how crews are built and deployed to any project; they are the source of truth.
- Never hand-edit `.kiro/agents/*.json`. Change source inputs, then rebuild with `just build .` (this repo) or `just build --all`.
- Don't add repo-specific build mechanics to shared steering/components unless every deployed project needs them.

## How this repo works

`base/crews/*.yaml` + `shared/components/*.yaml` are the source of truth. Never edit generated `.json` files directly.

```
base/              Base templates
  crews/              Generic crew definitions (12 crews, 78 agents total)
shared/               Shared resources across all projects
  components/         Component system (15 behavioral concerns)
  skills/             Shared skills
  steering/           Universal + persona-specific steering
.crews/               This repo's own crew config + evals
fleet.local.yaml      Project registry (name→path, gitignored)
generate.py           .crews/crew.yaml → .kiro/ output
bin/agent-crews       CLI wrapper for cross-project use
```

## Architecture: 3-Level Hierarchy

Every deployed project uses a 3-level agent hierarchy:

```
Dispatcher (depth 0) → Crew Lead (depth 1) → Worker (depth 2)
```

| Depth | Archetype | Role | Tools |
|-------|-----------|------|-------|
| 0 | `dispatcher` | Routes by intent to the right crew | `subagent`, `read`, `todo_list` |
| 1 | `orchestrator` | Plans and delegates within one crew | `subagent`, `todo_list` |
| 2 | `worker` | Executes tasks, produces artifacts | `read`, `write`, `shell` |

**Guardrails (enforced at build time):**
- Workers cannot have `subagent` (no delegation)
- Orchestrators cannot target other orchestrators (no lateral dispatch)
- Orchestrators should not have `read` (warning) — delegate reading to workers
- Only dispatchers can target orchestrators

## Crews (78 agents across 12 crews)

| Crew | Lead | Agents | Best For |
|------|------|:------:|----------|
| General | `/agent general-lead` | 14 | Mixed work, features |
| Bug Fix | `/agent bugfix-lead` | 8 | Bug fixing, testing |
| Infrastructure | `/agent infrastructure-lead` | 7 | Deploy, IaC |
| Research | `/agent research-lead` | 7 | Investigation, docs |
| Onboarding | `/agent onboarding-lead` | 6 | Brownfield repos |
| Hygiene | `/agent hygiene-lead` | 6 | Project maintenance |
| Content | `/agent content-lead` | 6 | Presentations, tutorials |
| Writing | `/agent writing-lead` | 6 | Writing, editing |
| Crew-Builder | `/agent crew-builder-lead` | 5 | Creating/modifying crews |
| Crew-Maintenance | `/agent crew-maintenance-lead` | 6 | Diagnosing, tuning, releasing |
| Crew-Tooling | `/agent crew-tooling-lead` | 3 | Fixing agent-crews scripts |
| Rust | `/agent rust-lead` | 4 | Rust-specific workflows |

### Composing a project's crews

`crews:` is a literal list — pick the crews that match the work. `general` is a sensible default for mixed work but is no longer auto-included. Specialized crews stand on their own.

## Common tasks

| Task | Command |
|------|---------|
| Generate all | `just build --all` |
| Generate one | `just build <project>` |
| Generate cwd | `just build .` |
| Fleet status | `just status` |
| Scan for projects | `just scan ~/code` |
| Push staging | `just push <project>` |
| Crew health check | `just check <project>` |
| Run evals | `just eval <project>` |
| Eval dry run | `just eval-dry <project>` |
| Session summary | `just summary <project>` |
| Cross-tool compare | `just compare <project>` |
| Ingest sessions | `just ingest <project>` |
| Migrate old layout | `just migrate <project>` |
| Smoke test | `just smoke-test <target-path>` |

## Post-Change Rule
After ANY modification to .crews/crew.yaml or base/crews/*.yaml, ALWAYS run `just build <project>` before considering the task complete.

## Deploy Checklist

Every project deployment MUST include a `@crew-sheet` prompt:
- Auto-generated at `<project>/.kiro/prompts/crew-sheet.md` by `just build`
- Lists all crews, agents, roles, and common tasks
- Uses the project's actual agent names (themed if theme is active)

## Agents (for this repo)

The dispatcher (`ctrl+shift+d`) is the entry point. It plans work, routes to crew leads, and self-executes simple commands. See `@crew-sheet` for the full roster.

```
Dispatcher (ctrl+shift+d) — plans, routes, reads context for routing
├── crew-builder-lead → crew-researcher, crew-creator, crew-augmenter
├── crew-maintenance-lead → crew-analyst, crew-doctor, crew-validator, project-hygiene, crew-releaser
├── crew-tooling-lead → meta-debugger, meta-tester
└── Shared utilities: verifier, editor, kiro-helper (available to all leads)
```

| Agent | Role |
|-------|------|
| dispatcher | Plans work, routes to leads, reads context for routing decisions |
| crew-builder-lead | Coordinates crew creation and modification |
| crew-maintenance-lead | Coordinates analysis, diagnosis, validation, releases |
| crew-tooling-lead | Coordinates debugging of agent-crews tooling |
| verifier | Independent verification before marking DONE |
| editor | Prose review, style enforcement |
| kiro-helper | CLI troubleshooting, MCP config |

Best practice: work on crews from this repo (centralized improvements). Use the dispatcher — it knows which lead to route to.

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
| `@grill-with-docs` | Design interrogation that updates CONTEXT.md and ADRs inline |
| `@thunderdome` | Ruthless editing — every feature fights to earn its place |

## Doc index

| Doc | What it covers |
|-----|---------------|
| [docs/use-case-guide.md](docs/use-case-guide.md) | Common workflows — how to use deployed agents |
| [docs/workspace.md](docs/workspace.md) | Workspace contract — ephemeral + durable roots, prompt substitution, handoff convention |
| [base/crews/](base/crews/) | Generic crew definitions (12 crews) |
| [shared/components/](shared/components/) | Component system (15 behavioral concerns) |
| [shared/skills/](shared/skills/) | Shared skills library |
| [docs/session-analysis.md](docs/session-analysis.md) | Multi-tool session analysis and crew recommendations |
| [docs/component-architecture/spec.md](docs/component-architecture/spec.md) | Component architecture specification |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records |
