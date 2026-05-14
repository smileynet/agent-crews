---
name: create-crew
description: Guide users through creating and deploying an agent crew to a new project. Ask relevant questions, help them make good choices about crews and configuration.
---

# Create Crew — Advisory Guide

## When a user wants to create a crew

Ask:
- What's the project path? (need to scan it)
- What kind of work do you primarily do in this project? (features, bugs, infra, research, writing)
- What's the build/test/lint setup? (or let me scan for it)
- Any commands that should be off-limits? (deploy, destroy, start servers)

## Step 1: Scan the project

Read to understand:
```bash
find <path> -maxdepth 3 -type f | grep -v .git | grep -v node_modules | sort
cat <path>/README.md
cat <path>/AGENTS.md 2>/dev/null
```

Look for build system:
- `.mise.toml`, `justfile`, `Makefile`, `package.json`, `pyproject.toml`, `Cargo.toml`, `cdk.json`

Check for existing agents:
```bash
find <path>/.kiro -type f 2>/dev/null
```

## Step 2: Help choose crews

Key considerations to surface:
- General is ALWAYS included — it's the baseline
- Only add specialized crews if the work genuinely benefits from domain-specific protocols
- More crews = more agents = more context for the user to manage
- Start minimal, add crews later if needed

| If they say... | Suggest |
|---------------|---------|
| "Mostly features and fixes" | Just general |
| "Lots of bug hunting" | general + bug-fix |
| "Heavy infrastructure work" | general + infrastructure |
| "Research-heavy, lots of docs" | general + research |
| "Brand new to this codebase" | general + onboarding (temporary) |
| "Maintenance mode" | general + hygiene |

## Step 3: Configure components

Ask:
- What are your build/test/lint commands?
- Do you want notifications? (toast, slack, discord)
- Git workflow: commit-and-push (solo) or PR-based (team)?
- Any theme preference? (or null for standard names)

## Step 4: Add to fleet.yaml

```yaml
projects:
  <project-name>:
    crews: [general]          # add specialized as needed
    theme: null
    components:
      verification:
        checks:
          build: "<build cmd>"
          test: "<test cmd>"
          lint: "<lint cmd>"
      git:
        variant: checkpoint   # or pr-based
```

## Step 5: Generate and deploy

```bash
just build
just link <project-name>
```

Verify agents appear:
```bash
ls <path>/.kiro/agents/
```

## Step 6: Recommend committing

Surface: "Commit `.kiro/` to your project so contributors get working agents without needing agent-crews."

## Common mistakes to prevent

- Don't omit general crew (mandatory baseline)
- Don't add every specialized crew "just in case" (start minimal)
- Don't forget to set build/test/lint commands (agents need these for verification)
- Don't set dangerous commands as allowed (deploy, destroy, rm -rf)
- Don't forget `just build` after fleet.yaml changes
