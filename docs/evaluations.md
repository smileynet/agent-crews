# Agent Evaluations

Test whether your agents behave correctly — route to the right specialist, stay in scope, follow protocols.

## Quick start

```bash
just eval              # run all evals
just eval-routing      # routing evals only
just eval-scope        # scope enforcement only
just eval-verbose      # show full agent output + judge reasoning
just eval-dry          # preview what would run (no invocations)
```

Results print to stdout and save to `results/eval-agent-crews-{timestamp}.json`.

## How it works

1. A test fixture defines: an agent, a prompt, and criteria for what good behavior looks like
2. The runner invokes the agent with the prompt via `kiro-cli`
3. A separate judge (bare kiro-cli, no agent personality) scores the output 1–5
4. Pass/fail is determined by a threshold (default ≥3, configurable per eval)

No regex matching, no exact string comparison — the judge evaluates behavioral intent.

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
    ideal: |                    # optional — anchors the judge
      Delegating to crew-augmenter — adding agents is their specialty.
    tags: [routing, meta-crew]  # for filtering
    threshold: 4                # override default ≥3
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Unique identifier (kebab-case) |
| `agent` | yes | Agent to invoke |
| `input` | yes | Prompt sent to the agent |
| `criteria` | yes | What the judge evaluates against |
| `ideal` | no | Reference answer — helps the judge calibrate |
| `tags` | no | For filtering (`--tag routing`) |
| `threshold` | no | Per-eval pass threshold (default: 3) |
| `timeout` | no | Seconds before timeout (default: 120) |

### Writing good criteria

- Describe behavior, not output format ("should delegate" not "should output JSON")
- Include what the agent should NOT do ("should not attempt the work itself")
- One eval tests one behavior — don't combine unrelated assertions
- If an eval flakes (>10% inconsistency), loosen the criteria

## Scoring

| Score | Meaning |
|-------|---------|
| 5 | Excellent — fully meets all criteria |
| 4 | Good — meets criteria with minor imperfections |
| 3 | Acceptable — meets core intent but with gaps |
| 2 | Poor — partially addresses criteria, misses key requirements |
| 1 | Fail — does not meet criteria |

## CLI options

```bash
uv run scripts/eval-crew.py                    # all evals
uv run scripts/eval-crew.py --tag routing      # filter by tag
uv run scripts/eval-crew.py --name <eval-name> # single eval
uv run scripts/eval-crew.py --threshold 4      # stricter pass threshold
uv run scripts/eval-crew.py --verbose          # show agent output + judge reasoning
uv run scripts/eval-crew.py --dry-run          # show what would run
```

## Results

Each run writes a JSON file to `results/` (gitignored):

```json
{
  "project": "agent-crews",
  "timestamp": "2026-05-13T21:00:00Z",
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 1,
    "errors": 1,
    "avg_score": 4.1
  },
  "results": [...]
}
```

Use these to track score trends over time and identify regressions.

## When to run evals

- After modifying crew YAML (routing changes, scope changes)
- After changing component steering (behavioral rules)
- Before releasing crew updates to projects
- Not on every commit — each eval costs ~$0.02–0.10 in model invocations

## Adding evals for your project

The default fixture tests the meta crew (this repo's own agents). To eval agents deployed to your project, create a separate fixture:

```bash
uv run scripts/eval-crew.py --fixture tests/my-project-evals.yaml
```

Same format, different agents and criteria.
