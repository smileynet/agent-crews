---
name: run-evals
description: Guide users through running and writing agent evaluations. Ask relevant questions, surface considerations, help them write effective criteria.
---

# Agent Evaluations — Advisory Guide

## When a user wants to run evals

Ask:
- Are you testing a specific change (routing, scope, component) or running a general health check?
- Have you modified crew YAML or steering recently?

Key considerations to surface:
- Each eval invokes the agent + a judge — costs ~$0.02–0.10 per eval
- Use `--tag` to scope runs when testing specific changes
- Use `--verbose` to see what the agent actually produced (essential for debugging)
- `--dry-run` shows what would execute without spending tokens

Commands:
```bash
uv run scripts/eval-crew.py              # all
uv run scripts/eval-crew.py --tag routing  # filtered
uv run scripts/eval-crew.py --verbose      # debug mode
```

## When a user wants to write a new eval

Ask:
- What behavior are you trying to verify? (routing, scope enforcement, protocol compliance)
- What would a correct response look like?
- What would a WRONG response look like? (this becomes the "should NOT" criteria)
- Is this testing one behavior or multiple? (split if multiple)

Key considerations to surface:
- Criteria should describe behavior, not output format
- Always include negative criteria (what the agent should NOT do)
- `ideal` field is optional but helps the judge calibrate on ambiguous cases
- Threshold 4 for critical behaviors (routing, scope), 3 for general compliance
- If an eval flakes, the criteria are too tight — loosen them

Fixture location: `tests/crew-evals.yaml`

## When evals fail

Ask:
- Did the agent produce wrong behavior, or did the judge score valid behavior too low?
- Run with `--verbose` — does the output look correct to you?

Considerations:
- Score 3 with correct behavior = criteria too strict, loosen
- Score 2 with wrong behavior = real issue, investigate the agent
- ERR status = agent timeout or empty output, not a scoring problem
- Check if crew YAML or steering changed recently (`git log --oneline -5 base/crews/ shared/components/`)

## Fixture format reference

```yaml
  - name: kebab-case-identifier
    agent: agent-name
    input: "Prompt sent to agent"
    criteria: |
      Should do X.
      Should NOT do Y.
    ideal: |              # optional
      Example correct response.
    tags: [routing]       # for filtering
    threshold: 4          # pass threshold (default 3)
    timeout: 120          # seconds
```
