---
name: create-crew
description: Guide for creating and deploying an agent crew to a new project. Uses helper scripts to minimize manual analysis.
---

# Create Crew

## Step 1: Scan project + sessions

Run both in sequence:
```bash
./scripts/project-scan.sh <project-path>
./scripts/session-summary.sh <project-path>
```

These give you everything: stack, build commands, existing agents, session history, intent distribution, token usage, and crew recommendations.

## Step 2: Choose crews

Use signals from both scripts:

| Signal | Crew to add |
|--------|-------------|
| `primary_intent: bugs` or `testing` | bug-fix |
| `primary_intent: infrastructure` | infrastructure |
| `primary_intent: research` or `documentation` | research |
| Heavy test suite (>10 test files) | bug-fix |
| Terraform/CDK/Docker files | infrastructure |
| High token usage + long sessions | consider task_tracking component |
| High failure rate (>15%) | add sanity_gate component |

General is ALWAYS included. Start minimal — add crews later if needed.

## Step 3: Configure

Build commands come from project-scan output. Add to fleet.yaml:
```yaml
projects:
  <name>:
    crews: [general, ...]  # from recommendation
    theme: null
    components:
      verification:
        checks:
          build: "<from scan>"
          test: "<from scan>"
          lint: "<from scan>"
```

## Step 4: Generate and deploy

```bash
just build
just link <project-name>
```

Verify: `ls projects/<name>/.kiro/agents/`

## Rules

- Never omit general crew
- Don't add crews without signal (static files OR session history)
- Always set build/test/lint from scan output
- Run `just build` after any fleet.yaml change
- If session data shows high token/session, enable task_tracking component
