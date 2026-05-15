---
name: configure-fleet
description: Guide users through .crews/crew.yaml configuration. Ask about their project, help them make good choices about crews, components, and deployment.
---

# Fleet Configuration — Advisory Guide

## When a user wants to configure a project

Ask:
- What's the project name and path?
- What language/framework? (determines build/test/lint commands)
- Solo or team workflow? (determines git variant)
- Any existing `.kiro/` in the project? (coexist or replace?)

## Key decisions to guide

### Crews

Surface: "Start with just general. What kind of work do you do most in this project?"

Only suggest additional crews if they describe work that clearly benefits:
- "I spend most of my time debugging" → suggest bug-fix
- "Heavy Terraform/CDK work" → suggest infrastructure
- "Lots of investigation and documentation" → suggest research

Don't suggest all crews. More isn't better.

### Verification commands

Ask: "What commands do you use to build, test, and lint?"

Key considerations to surface:
- These should be FAST commands (agents run them frequently)
- `cargo check` over `cargo build` (faster)
- `npm run build` not `npm start` (build, don't serve)
- Set to `null` if the project doesn't have one
- Dangerous commands (deploy, destroy) should NEVER be here

### Git variant

Ask: "Do you work solo on this project, or is it a team repo with PRs?"

- Solo → `checkpoint` (commit and push immediately)
- Team → `pr-based` (branch, commit, open PR)

### Notifications

Ask: "Do you want to be notified when agents finish tasks?"

- `toast` — OS notification (default, low friction)
- `slack` — requires webhook URL
- `discord` — requires webhook URL
- Policy `completions` = only on done/failed (recommended)
- Policy `verbose` = also on milestones and blockers

### Theme

Only mention if the user seems interested in customization. It's cosmetic — doesn't affect behavior.

## fleet.local.yaml

Ask: "Where does this project live on your machine?"

```yaml
projects:
  project-name: /absolute/path/to/project
```

This is gitignored — it's per-machine configuration.

## After configuration

Remind:
1. `just build` to generate
2. `just link <project>` to deploy
3. Commit `.kiro/` in the target project for durability
