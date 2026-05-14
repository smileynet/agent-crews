---
description: "Regenerate and deploy an agent team to its target project"
---

# Deploy Crew

Regenerate and deploy agents to a target project.

## Parameters

- `project` (required): Project name in `projects/` (e.g., `my-project`)

## Steps

1. Run `just build` (regenerates all projects)
2. Run `just link <project>` (symlinks to target)
3. Verify: confirm `.kiro/agents/` exists in target project
4. Display deployed agent count and crew-sheet pointer

## Output

```
✅ Deployed <project>
   Agents: <N>
   Target: <path from fleet.local.yaml>
   Reference: @crew-sheet
```
