# Creating Crews

Deploy an agent crew to any kiro-cli project.

## The easy way

```bash
cd agent-crews
kiro-cli chat -A --agent dispatcher
# "Create a crew for ~/code/my-project"
```

The dispatcher delegates to crew-creator, which reads your project, picks crews, configures components, and deploys.

## What happens during crew creation

1. **Project scan** — reads your repo structure, build system, conventions
2. **Crew selection** — picks which crews fit (general is always included)
3. **Configuration** — sets build/test/lint commands, component preferences
4. **Generation** — assembles agents from crew YAML + components + steering
5. **Deployment** — links or copies `.kiro/` to your project

## Choosing crews

Every project gets `general`. Add specialized crews based on your primary work:

| Primary work | Add crew |
|-------------|----------|
| Bug fixing | bug-fix |
| Infrastructure / deploy | infrastructure |
| Research / investigation | research |
| New to codebase | onboarding |
| Maintenance / cleanup | hygiene |
| Presentations / tutorials | content |
| Writing / editing | writing |

A project can have multiple specialized crews alongside general.

## Configuration

Your project's config lives in `fleet.yaml`:

```yaml
projects:
  my-project:
    crews: [general, research]
    theme: null
    components:
      verification:
        checks:
          build: "npm run build"
          test: "npm test"
          lint: "npx eslint ."
```

The generator uses this to assemble the right agents with the right behavioral rules.

## Deploying

```bash
just build              # generate all projects
just link my-project    # symlink to target project
```

Or use `@deploy-crew` to have an agent handle it.

## Updating

When you change crew definitions or components:

```bash
just build
just link my-project
```

Then commit the updated `.kiro/` in your project repo.
