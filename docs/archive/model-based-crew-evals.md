# Spec: Model-Based Crew Evaluations

**Status:** Planned
**Date:** 2026-05-13

## Objective

Replace regex-based smoke tests with model-based evaluation. Use kiro-cli (bare, no agent) as a judge to evaluate whether agent output meets behavioral criteria defined in test fixtures. Likert 1-5 scoring gives gradient signal for trend tracking and criteria calibration.

## Architecture

```
tests/crew-evals.yaml        Test fixtures (input + criteria + optional ideal)
        │
scripts/eval-crew.py         Test runner (Python, uv run)
        │
        ├─── kiro-cli chat --no-interactive --agent X    (agent under test)
        │
        └─── kiro-cli chat --no-interactive              (judge, no agent)
        │
results/eval-{project}-{timestamp}.json    Per-run results
```

## Decisions

| # | Decision | Rationale |
|---|----------|----------|
| 1 | Python runner via `uv run` | YAML parsing, JSON handling, structured output — matches project convention |
| 2 | kiro-cli for both agent and judge | Same tool, swap judge later for diversity |
| 3 | Judge runs with no `--agent` flag | Neutral evaluator, no crew personality contamination |
| 4 | Full agent output, ANSI-stripped, inline in positional arg | Judge needs full context to see delegation signals |
| 5 | Likert 1-5 scale with configurable pass threshold | Gradient signal, trend tracking, criteria calibration |
| 6 | Default threshold ≥3, per-eval override, `--threshold` CLI flag | 3 = acceptable for smoke tests, tighten for critical evals |
| 7 | Meta crew only for v1, target-project evals as fast-follow | Validate approach before expanding scope |
| 8 | Stdout + per-run JSON file to `results/` (gitignored) | Immediate feedback + persistent trend data |
| 9 | Filename: `eval-{project}-{timestamp}.json` | Scannable in ls, queryable by tools |
| 10 | Single fixture file for v1 | ~20 evals fits one file; split later if >50 |
| 11 | Sequential execution | Avoids session interference, simpler debugging |
| 12 | Judge prompt: domain preamble + rubric + optional ideal | Anchors judge with context and reference answers |
| 13 | No agent system prompt in judge context | Criteria are self-contained; avoids bloat |
| 14 | Retry once on agent failure, then ERROR (no score) | Handles transient failures without polluting scores |

## Test Fixture Format

```yaml
# tests/crew-evals.yaml
evals:
  - name: test-identifier-kebab-case
    agent: agent-name
    input: "The prompt sent to the agent"
    criteria: |
      Natural language description of expected behavior.
      Can include positive (should do X) and negative (should NOT do Y).
    ideal: |                    # optional — reference answer for judge anchoring
      Example of what a correct response looks like.
    tags: [routing, meta-crew]  # optional, for filtering
    threshold: 4                # optional, overrides default ≥3
    timeout: 120                # optional, seconds, default 120
```

### Criteria Writing Guidelines

- Write as behavioral expectations, not output format requirements
- Include both positive and negative criteria
- Be specific enough to distinguish correct from incorrect, but broad enough for valid paraphrases
- One eval tests one behavior (don't combine unrelated assertions)
- If an eval flakes (>10% inconsistency), loosen the criteria

## Scoring

### Likert Scale

| Score | Meaning |
|-------|---------|
| 5 | Excellent — fully meets all criteria, clear and well-executed |
| 4 | Good — meets all criteria with minor imperfections |
| 3 | Acceptable — meets core intent but with notable gaps |
| 2 | Poor — partially addresses criteria but misses key requirements |
| 1 | Fail — does not meet criteria |

### Pass Threshold

- Default: ≥3
- Per-eval override via `threshold` field in fixture
- Global override via `--threshold` CLI flag
- Critical evals (routing, scope) should use threshold: 4

## Judge Prompt Template

```
You are evaluating an AI agent from a multi-agent crew system. Agents have specific roles: orchestrators route work to specialists, workers execute tasks within their scope.

## Evaluation Task
Rate how well the agent output satisfies the criteria.

## Criteria
{criteria}

{ideal_section}

## Agent Output
{output}

## Scoring Rubric
5 = Excellent — fully meets all criteria, clear and well-executed
4 = Good — meets all criteria with minor imperfections (e.g., slightly verbose, minor omission)
3 = Acceptable — meets the core intent but with notable gaps (e.g., correct routing but no narration)
2 = Poor — partially addresses criteria but misses key requirements (e.g., does the work itself instead of delegating)
1 = Fail — does not meet criteria (e.g., wrong agent, ignores scope, hallucinates)

Respond with exactly two lines:
SCORE: <number>
REASON: <one sentence explanation>
```

When `ideal` is provided, `{ideal_section}` becomes:
```
## Reference (ideal response)
{ideal}
Note: The agent does not need to match this exactly. Use it as a reference for what correct behavior looks like.
```

When `ideal` is absent, `{ideal_section}` is empty.

## Error Handling

### Agent Failures

1. Agent invocation fails (crash, timeout, empty output)
2. Retry once (same invocation)
3. If retry succeeds → proceed to judge as normal
4. If retry also fails → record as ERROR (no numeric score)

### Error Statuses

| Status | Meaning |
|--------|---------|
| `evaluated` | Judge scored the output normally |
| `error` | Agent failed on both attempts (not scored) |

Errors are reported separately and do not affect the pass/fail count or average score.

## Test Runner

File: `scripts/eval-crew.py` (invoked via `uv run scripts/eval-crew.py`)

### Usage

```bash
# Run all evals
uv run scripts/eval-crew.py

# Filter by tag
uv run scripts/eval-crew.py --tag routing
uv run scripts/eval-crew.py --tag scope

# Run single eval by name
uv run scripts/eval-crew.py --name dispatcher-routes-augment

# Override threshold
uv run scripts/eval-crew.py --threshold 4

# Dry run (show what would run, no invocations)
uv run scripts/eval-crew.py --dry-run

# Verbose (show full agent output + judge reasoning)
uv run scripts/eval-crew.py --verbose
```

### Output Format (stdout)

```
[ 5 ] dispatcher-routes-augment: Correctly delegated with narration
[ 4 ] dispatcher-routes-researcher: Delegated correctly, slightly verbose
[ 2 ] dispatcher-refuses-app-code: Attempted partial fix before refusing
[ERR] kiro-helper-knows-tools: timeout (2 attempts)
---
Results: 8/9 passed (threshold: ≥3), avg score: 4.1
Errors: 1 (not scored)
```

### Results File

Written to `results/eval-{project}-{timestamp}.json` (gitignored):

```json
{
  "project": "agent-crews",
  "crews": ["meta"],
  "timestamp": "2026-05-13T21:00:00Z",
  "pass_threshold": 3,
  "duration_s": 185.4,
  "summary": {
    "total": 10,
    "evaluated": 9,
    "passed": 8,
    "failed": 1,
    "errors": 1,
    "avg_score": 4.1
  },
  "results": [
    {
      "name": "dispatcher-routes-augment",
      "score": 5,
      "status": "evaluated",
      "reason": "Correctly delegated to crew-augmenter with clear narration",
      "duration_s": 8.2
    },
    {
      "name": "kiro-helper-knows-tools",
      "score": null,
      "status": "error",
      "error": "timeout",
      "reason": "Exceeded 120s on both attempts",
      "duration_s": 240.0
    }
  ]
}
```

### Exit Codes

- 0: all evaluated evals pass threshold
- 1: one or more evaluated evals below threshold
- 2: configuration error (invalid YAML, missing fixture file)

## Test Categories (v1 — meta crew)

### 1. Routing

| Eval | Input | Expected Behavior | Threshold |
|------|-------|-------------------|-----------|
| dispatcher-routes-augment | "add a new agent to the general crew" | Delegates to crew-augmenter | 4 |
| dispatcher-routes-researcher | "research testing patterns for Godot" | Delegates to crew-researcher | 4 |
| dispatcher-routes-doctor | "my agents aren't validating" | Delegates to crew-doctor | 4 |
| dispatcher-routes-analyst | "review my last session" | Delegates to crew-analyst | 4 |
| dispatcher-routes-hygiene | "check data separation" | Delegates to project-hygiene | 4 |
| dispatcher-routes-creator | "build a crew for ~/code/myproject" | Delegates to crew-creator | 4 |

### 2. Scope Enforcement

| Eval | Agent | Input | Expected Behavior | Threshold |
|------|-------|-------|-------------------|-----------|
| dispatcher-refuses-app-code | dispatcher | "fix the login bug in my React app" | Refuses, explains scope | 4 |
| dispatcher-asks-clarification | dispatcher | "help me with my project" | Asks clarifying question | 3 |

### 3. Component Behaviors

| Eval | Component | Agent | Input | Expected Behavior |
|------|-----------|-------|-------|-------------------|
| troubleshooting-escalation | troubleshooting | crew-augmenter | "tried 3 times, same error" | Suggests different approach |
| verification-knows-commands | verification | crew-creator | "what build commands?" | References project-specific commands |

### 4. Agent Identity

| Eval | Agent | Input | Expected Behavior |
|------|-------|-------|-------------------|
| project-hygiene-knows-checks | project-hygiene | "what do you check?" | Lists ≥3 of 5 check categories |
| crew-researcher-knows-procedure | crew-researcher | "how do you work?" | Mentions scope/fetch/process/frame |
| kiro-helper-knows-tools | kiro-helper | "what can you help with?" | Mentions MCP, agent config, tool naming |

## Cost Estimate

- Agent invocation: ~$0.01-0.05 per test (kiro-cli model)
- Judge invocation: ~$0.01-0.05 per test (kiro-cli model)
- Full suite (20 evals): ~$0.40-2.00 per run
- Recommended: run on-demand, not on every push

## Flake Handling

- Criteria should be broad enough that valid responses always pass
- If a test flakes (>10% inconsistency), loosen the criteria
- A consistently failing test = real crew issue
- No automatic retry for scoring (retry is only for agent invocation failures)
- Track flake rate by comparing scores across runs in results/

## Integration

- `just eval` — run all evals
- `just eval-routing` — run routing evals only
- `just eval-scope` — run scope evals only
- Replaces `just smoke-test` for behavioral validation
- `scripts/validate.sh` remains for structural checks (no LLM needed)

## Fast-Follows

1. **Target-project evals** — test component behaviors in deployed projects (separate fixture files per project)
2. **Parallel execution** — `--parallel N` flag for faster runs
3. **Judge diversity** — swap kiro-cli judge for direct API call (different model, temperature 0)
4. **Auto-generated evals** — derive criteria from agent system prompts automatically
5. **Trend dashboard** — script that reads results/ and shows score trends over time

## Implementation Plan

1. Create `tests/crew-evals.yaml` with ~20 evals (routing, scope, identity, components)
2. Create `scripts/eval-crew.py` (runner: parse YAML, invoke agent, invoke judge, parse score, write results)
3. Add `results/` to `.gitignore`
4. Add `just eval` recipe to justfile
5. Run, tune criteria until stable (<5% flake rate)
6. Document in CONTRIBUTING.md

## Done Criteria

- [ ] `tests/crew-evals.yaml` exists with ≥20 evals
- [ ] `scripts/eval-crew.py` runs and produces scored output
- [ ] `just eval` works
- [ ] Results written to `results/eval-agent-crews-{timestamp}.json`
- [ ] All evals pass on current crew (baseline established)
- [ ] Flake rate <5% over 3 consecutive runs
- [ ] Documented in CONTRIBUTING.md
