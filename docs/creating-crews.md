# Creating Crews

Deploy an agent crew to any project.

## The easy way

```bash
cd agent-crews
kiro-cli chat -A --agent dispatcher
# "Create a crew for ~/code/my-project"
```

The dispatcher delegates to crew-creator, which scans your project, analyzes session history, picks crews, and generates agents.

## What happens during crew creation

1. **Project scan** (`./scripts/project-scan.sh`) — detects stack, build tools, structure
2. **Session analysis** (`./scripts/session-summary.sh`) — analyzes work patterns across all AI tools
3. **Crew selection** — picks crews based on intent distribution and project signals
4. **Configuration** — writes `.crews/crew.yaml` with full self-contained config
5. **Generation** — assembles `.kiro/` output (agents, prompts, steering)
6. **Push** — copies `.crews/` + `.kiro/` to your project

## Choosing crews

Pick whichever crews match your work. `general` is a sensible default but no longer mandatory.

| Signal | Add crew |
|--------|----------|
| >30% bugs/testing in sessions | bug-fix |
| >30% research/docs in sessions | research |
| >20% infrastructure in sessions | infrastructure |
| Heavy test suite (>10 test files) | bug-fix |
| Terraform/CDK/Docker files | infrastructure |
| No session data — user says "bug hunting" | bug-fix |

Start minimal. Add crews later if needed.

## Configuration

Your project's config lives in `.crews/crew.yaml` (self-contained, no inheritance):

```yaml
# ~/code/my-project/.crews/crew.yaml
crews: [general, research]
behavior:
  verification:
    variant: gate
    checks:
      build: "npm run build"
      test: "npm test"
      lint: "npx eslint ."
  git:
    variant: checkpoint
```

## Rebuilding

```bash
# From agent-crews
just build my-project

# From the project itself
agent-crews build
```

## What gets created

```
~/code/my-project/
  .crews/          ← source (commit this)
    crew.yaml
    evals.yaml
    scripts/
  .kiro/           ← generated output
    agents/*.json
    prompts/*.md
    steering/**/*.md
```
