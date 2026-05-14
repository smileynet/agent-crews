# Agent Evaluations

Test whether your agents behave correctly — route to the right specialist, stay in scope, follow protocols.

## What evals do

Evals send a prompt to an agent and have a separate judge score the response against criteria you define. No regex, no exact string matching — the judge evaluates behavioral intent on a 1–5 scale.

## When to run them

- After modifying crew YAML (routing, scope changes)
- After changing component steering (behavioral rules)
- Before releasing crew updates to projects
- Not on every commit — each eval costs ~$0.02–0.10 in model invocations

## Running evals

```bash
just eval              # all evals
just eval-routing      # routing evals only
just eval-scope        # scope enforcement only
just eval-verbose      # show full agent output + judge reasoning
just eval-dry          # preview what would run
```

Results print to stdout and save to `results/`.

## Writing evals

Evals live in `tests/crew-evals.yaml`:

```yaml
evals:
  - name: dispatcher-routes-augment
    agent: dispatcher
    input: "add a new agent to the general crew"
    criteria: |
      The response should delegate to crew-augmenter.
      It should narrate the routing decision.
      It should NOT attempt to write YAML itself.
    tags: [routing, meta-crew]
    threshold: 4
```

### Tips for good criteria

- Describe behavior, not output format ("should delegate" not "should output JSON")
- Include what the agent should NOT do
- One eval tests one behavior
- If an eval flakes (>10%), loosen the criteria

## Scoring

| Score | Meaning |
|-------|---------|
| 5 | Excellent — fully meets all criteria |
| 4 | Good — minor imperfections |
| 3 | Acceptable — meets core intent with gaps |
| 2 | Poor — misses key requirements |
| 1 | Fail — does not meet criteria |

Default pass threshold is ≥3. Critical evals (routing, scope) should use threshold: 4.

## Results

Each run saves a JSON file to `results/` with scores, reasons, and timing. Use these to track regressions over time.
