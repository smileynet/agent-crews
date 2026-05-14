---
name: run-evals
description: Process for running and writing model-based agent evaluations. Use when testing agent behavior, adding new evals, or diagnosing regressions.
---

# Run Evaluations Process

## Running evals

```bash
# All evals
uv run scripts/eval-crew.py

# Filter by tag
uv run scripts/eval-crew.py --tag routing

# Single eval
uv run scripts/eval-crew.py --name dispatcher-routes-augment

# Stricter threshold
uv run scripts/eval-crew.py --threshold 4

# Show agent output + judge reasoning
uv run scripts/eval-crew.py --verbose

# Preview without running
uv run scripts/eval-crew.py --dry-run
```

## Writing a new eval

### Step 1: Identify the behavior to test

One eval = one behavior. Examples:
- Dispatcher routes "add an agent" to crew-augmenter
- Dispatcher refuses out-of-scope work
- Agent follows troubleshooting escalation protocol

### Step 2: Write the fixture

Add to `tests/crew-evals.yaml`:

```yaml
  - name: descriptive-kebab-case-name
    agent: agent-name
    input: "The exact prompt to send"
    criteria: |
      What the agent SHOULD do.
      What the agent should NOT do.
      Specific signals to look for.
    ideal: |                    # optional — reference for judge calibration
      Example of correct behavior.
    tags: [category]            # routing, scope, components, identity
    threshold: 4                # 3 = acceptable, 4 = strict
    timeout: 120                # seconds, default 120
```

### Step 3: Dry run to verify

```bash
uv run scripts/eval-crew.py --name your-new-eval --dry-run
```

### Step 4: Run and calibrate

```bash
uv run scripts/eval-crew.py --name your-new-eval --verbose
```

If the eval fails but the agent behavior looks correct, loosen the criteria. If it passes but the behavior is wrong, tighten the criteria.

### Step 5: Run full suite to check for interference

```bash
uv run scripts/eval-crew.py
```

## Fixture fields

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Unique identifier (kebab-case) |
| `agent` | yes | Agent to invoke |
| `input` | yes | Prompt sent to the agent |
| `criteria` | yes | What the judge evaluates against |
| `ideal` | no | Reference answer — helps judge calibrate |
| `tags` | no | For filtering (`--tag routing`) |
| `threshold` | no | Per-eval pass threshold (default: 3) |
| `timeout` | no | Seconds before timeout (default: 120) |

## Interpreting results

- **Score 5**: Agent nailed it
- **Score 4**: Correct behavior, minor style issues
- **Score 3**: Right direction, missing signals (e.g., routed correctly but no narration)
- **Score 2**: Partially correct but missed the point
- **Score 1**: Wrong behavior entirely
- **ERR**: Agent timed out or produced empty output (not scored)

## Results files

Written to `results/eval-agent-crews-{timestamp}.json`. Fields:
- `summary.passed` / `summary.failed` — count
- `summary.avg_score` — trend indicator
- `results[].reason` — judge's one-line explanation

## Diagnosing failures

1. Run with `--verbose` to see full agent output
2. Check if the criteria are too strict (valid behavior scored low)
3. Check if the agent prompt/steering changed (expected behavior shifted)
4. Check if the judge is miscalibrating (compare ideal vs actual)

## Exit codes

- 0: all evaluated evals pass
- 1: one or more below threshold
- 2: configuration error (bad YAML, missing fixture)
