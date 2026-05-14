# agent-crews

Multi-agent crews for [kiro-cli](https://github.com/kiro-cli) projects. Deploy a team of specialized AI agents to any coding project in under a minute.

## Quick Start

```bash
# 1. Configure your projects
cp fleet.example.yaml fleet.yaml
# Edit fleet.yaml — add your projects, set build/test/lint commands

# 2. Generate agents
just build

# 3. Deploy to your project
just link <project-name>
```

Then in your project:
```bash
kiro-cli chat
/agent general-lead     # "I'm building features"
```

The lead delegates to specialists automatically.

## Pick the Right Crew

| I'm doing... | Command |
|--------------|--------|
| Features, mixed work | `/agent general-lead` |
| Fixing bugs | `/agent bugfix-lead` |
| Deploying infrastructure | `/agent infrastructure-lead` |
| Research / docs | `/agent research-lead` |
| Onboarding to new codebase | `/agent onboarding-lead` |
| Project hygiene | `/agent hygiene-lead` |
| Presentations / tutorials | `/agent content-lead` |
| Writing / editing | `/agent writing-lead` |

Want themed names? Add `theme: wow` in your fleet.yaml. See [Themed Crews Guide](docs/themed-crews-guide.md).

## How It Works

```
fleet.example.yaml    Reference configuration (copy to fleet.yaml)
base/crews/           8 generic crew definitions (source of truth)
shared/components/    14 behavioral concerns (verification, git, troubleshooting, etc.)
shared/themes/        Optional cosmetic overlays (rename agents, add voice)
shared/skills/        On-demand knowledge for agents
generate.py           Assembles crews + components + theme → deployable agents
```

1. Crew YAMLs define agent rosters and delegation rules
2. Components define behavioral rules (delivered via steering files)
3. Theme overlays rename agents cosmetically (optional, per-project)
4. Generator assembles everything into `.kiro/agents/*.json` + steering
5. `just link <project>` deploys to your project

See `examples/` for complete generated output showing what gets deployed.

## Configuration

Edit `fleet.yaml` (copied from `fleet.example.yaml`):

```yaml
projects:
  my-project:
    crews: [general, research]    # general is always required
    theme: null                   # or: wow, starcraft, nautical, etc.
    components:
      verification:
        checks:
          build: "cargo check"
          test: "cargo test"
          lint: "cargo clippy"
```

See [fleet.example.yaml](fleet.example.yaml) for the full format with all options.

## Common Commands

| Task | Command |
|------|--------|
| Generate all | `just build` |
| Deploy to project | `just link <project>` |
| Fleet status | `just status` |
| Validate | `just check` |
| Run evals | `just eval` |

## Documentation

| Audience | Start here |
|----------|-----------|
| **Users** — deploying agents to your projects | [Use Case Guide](docs/use-case-guide.md) |
| **Developers** — contributing crews, components, skills | [CONTRIBUTING.md](CONTRIBUTING.md) |

### Further reading

- [Component Architecture](docs/component-architecture/spec.md) — how behavioral rules work
- [Themed Crews Guide](docs/themed-crews-guide.md) — game-themed agent names
- [Architecture Decisions](docs/decisions/) — why things are the way they are
- [Examples](examples/) — generated output for reference projects

## Design Principles

- Agents are specialized — each does one thing well
- Generic names by default — themes are opt-in cosmetic overlays
- Behavioral rules live in components — change once, regenerate all
- Crew YAML is the source of truth — never edit generated JSON
- `fleet.yaml` is gitignored — your projects stay private

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, conventions, and how to add crews/components/skills.

Found a bug? [Open an issue](../../issues/new?template=bug_report.yml).  
Have an idea? [Request a feature](../../issues/new?template=feature_request.yml).

## License

[MIT](LICENSE)
