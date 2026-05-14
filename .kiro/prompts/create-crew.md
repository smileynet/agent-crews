---
description: "Deploy agent crew to a project — detects stack, configures components, generates and links"
---

# Create Crew

Deploy an agent team to a target project.

## Parameters

- `project_path` (required): Path to the target project (e.g., `~/code/my-project`)

## Steps

1. Read the target project: structure, README, build config, test runner
2. Detect: language, framework, build system (`mise`/`just`/`make`/`npm`/`cargo`)
3. Check for existing `.kiro/` — if present, confirm before overwriting
4. Determine project name (directory basename)
5. Add project to `fleet.yaml` under `projects:` with:
   - `type: themed` (uses base crews) or `type: custom` (if unusual structure)
   - Component overrides for `verification.checks` (detected build/test/lint commands)
   - Git workflow (`checkpoint` for solo, `pr-based` if team repo)
6. Add deployment path to `fleet.local.yaml`
7. Create `projects/<name>/.kiro/crew.yaml` if custom, otherwise base crews sync automatically
8. Create `projects/<name>/.kiro/steering/project.md` with project context
9. Run `just build` (generates agents + steering + scripts)
10. Run `just link <name>` (symlinks to target project)
11. Verify: confirm `.kiro/agents/` exists in target project
12. Display post-deploy onboarding (see Output)

## Output

```
✅ Deployed to <project_path>/.kiro

🎯 Your crews (56 agents across 8 crews):
  /agent raid-leader    — features, mixed work
  /agent handler        — bug fixing
  /agent commander      — infrastructure
  /agent sage           — research, docs

🚀 Start here:
  cd <project_path>
  kiro-cli chat
  /agent raid-leader
  "Help me <suggested task based on project>"

📋 Full reference: @crew-sheet
```

## Key Files Modified

- `fleet.yaml` — project added to registry
- `fleet.local.yaml` — deployment path added
- `projects/<name>/.kiro/` — generated output (agents, steering, scripts)
- Target project `.kiro/` — symlinked to above
