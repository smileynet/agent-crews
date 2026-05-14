# agent-crews

Your AI coding assistant is one agent doing everything. Give it a team instead.

agent-crews deploys specialized AI agent teams to [kiro-cli](https://github.com/kiro-cli) projects. Each crew has a lead that delegates to specialists — a builder, a tester, a researcher, a reviewer — so you talk to one agent and get the output of many.

## What you can do

- **Build features** — a lead plans the work, delegates implementation, testing, and review
- **Fix bugs** — a specialist reproduces, diagnoses root cause, applies minimal fix, verifies
- **Research & document** — agents investigate code, draft docs, fact-check claims
- **Deploy infrastructure** — plan, provision, verify health, report status
- **Onboard to a codebase** — scan architecture, trace dependencies, produce a guide
- **Write & present** — outline, draft, edit, format

Pick the crew that matches your work:

| I'm doing... | Start with |
|--------------|-----------|
| Features, mixed work | `/agent general-lead` |
| Fixing bugs | `/agent bugfix-lead` |
| Infrastructure / deploy | `/agent infrastructure-lead` |
| Research / docs | `/agent research-lead` |
| Onboarding to new codebase | `/agent onboarding-lead` |
| Project maintenance | `/agent hygiene-lead` |
| Presentations / tutorials | `/agent content-lead` |
| Writing / editing | `/agent writing-lead` |

## Getting started

```bash
# 1. Clone and configure
git clone <this-repo>
cp fleet.example.yaml fleet.yaml
# Edit fleet.yaml — add your project, pick crews, set build/test/lint commands

# 2. Generate agents
just build

# 3. Deploy to your project
just link my-project
```

Then in your project:
```bash
kiro-cli chat
/agent general-lead
```

The lead delegates to specialists automatically. See the [Use Case Guide](docs/use-case-guide.md) for workflows.

### Minimal fleet.yaml

```yaml
projects:
  my-project:
    crews: [general, research]
    components:
      verification:
        checks:
          build: "npm run build"
          test: "npm test"
          lint: "npx eslint ."
```

`general` is always required. Add specialized crews alongside it.

### What to commit in your project

After deploying, commit the generated `.kiro/` directory to your project repo:

```bash
cd ~/code/my-project
git add .kiro/
git commit -m "chore: add agent crew"
```

This gives every contributor working agents out of the box. The generated files are the final artifact — you don't need agent-crews installed to use them.

To update later: re-run `just build` + `just link my-project` in this repo, then commit the updated `.kiro/` in your project.

## How it works

Crew YAMLs define agent rosters and delegation rules. A generator assembles them with behavioral components (verification, git workflow, troubleshooting, etc.) into deployable `.kiro/agents/*.json` + steering files.

- [Component system](docs/component-architecture/spec.md) — behavioral rules that apply across all agents
- [Themed crews](docs/themed-crews-guide.md) — optional cosmetic overlays (game-themed agent names)
- [Generation workflow](CONTRIBUTING.md#workflow) — how to modify and regenerate crews
- [Architecture decisions](docs/decisions/) — why things are the way they are
- [Examples](examples/) — complete generated output for reference projects

## Commands

| Task | Command |
|------|--------|
| Generate all | `just build` |
| Deploy to project | `just link <project>` |
| Fleet status | `just status` |
| Validate | `just check` |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and conventions.

[Report a bug](../../issues/new?template=bug_report.yml) · [Request a feature](../../issues/new?template=feature_request.yml)

## License

[MIT](LICENSE)
