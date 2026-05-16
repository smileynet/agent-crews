# ADR-010: Eval Harness Design

**Status:** Accepted  
**Date:** 2026-05-16  
**Context:** We need behavioral evaluations for the meta crew to catch regressions, validate routing, and ensure agents follow their protocols.

## Decision

Build a model-based eval harness (`scripts/eval-crew.py`) that invokes agents via kiro-cli and grades responses with an LLM judge.

## Key Design Decisions

### 1. LLM-as-Judge (not code-based grading)

**Chosen:** LLM judge with structured rubric (5-point Likert scale).  
**Rejected:** Code-based grading (regex, string match).  
**Why:** Agent responses are free-form text. Routing evals need to detect *intent* to delegate, not exact string matches. Code-based grading is too brittle for behavioral evaluation.  
**Tradeoff:** Non-deterministic scoring. Mitigated by multi-trial and majority-vote.

### 2. Isolation (mktemp per eval)

**Chosen:** Every eval runs in a fresh temp directory with symlinked read-only context.  
**Rejected:** Shared cwd (faster but state leaks between evals).  
**Why:** Agents can write files. Without isolation, one eval's side effects corrupt the next. The 8s overhead across 39 evals is negligible vs. the debugging cost of correlated failures.

### 3. Default 3 trials (pass^k)

**Chosen:** Run each eval 3 times, require ALL to pass.  
**Rejected:** Single trial (fast but untrustworthy).  
**Why:** LLM non-determinism means a single score is noise. pass^3 catches agents that only route correctly sometimes. Use `--trials 1` for fast iteration.  
**Tradeoff:** 3x runtime. Acceptable for CI; developers use `--trials 1` locally.

### 4. Retry policy

**Agent retries:**
- 1 retry on empty output or timeout (transient infrastructure failure)
- No retry on non-empty output (agent responded — judge it as-is)

**Judge retries:**
- 1 retry on parse failure (judge gave unparseable output)
- No retry on valid score (even if low — that's signal, not noise)

**Why:** Retrying a bad *response* would mask real failures. Only retry when the failure is clearly infrastructure (empty/timeout/parse error), not behavioral.

### 5. Criteria structure (PRIMARY + AUTOMATIC FAIL)

**Chosen:** Each eval has one PRIMARY signal and an explicit AUTOMATIC FAIL condition.  
**Rejected:** Multi-dimensional criteria scored on a single axis.  
**Why:** Per Anthropic's eval best practices, the judge needs unambiguous pass/fail signals. Multi-dimensional criteria force the judge to weight competing signals — that's where scoring variance comes from.  
**Source:** https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

### 6. Threshold rationale

- `threshold: 4` — Correctness-critical (routing, scope, safety). Wrong answer = broken system.
- `threshold: 3` — Quality-oriented (identity, narration, style). Partial credit acceptable.

### 7. Results storage (per-run directories)

**Chosen:** `results/runs/<timestamp>/meta.json` + `scores.jsonl`  
**Rejected:** Flat files (`eval-project-timestamp.json`), SQLite.  
**Why:** Per-run dirs are self-contained, diffable, greppable. JSONL is one line per eval — trivially parseable. SQLite adds a dependency for marginal query benefit.

**meta.json captures:** git commit, branch, kiro-cli version, fixture SHA, config, summary.  
**scores.jsonl captures:** per-eval name, score, reason, duration, trial_scores.  
**Deliberately omitted:** Full agent output (large, privacy risk), system env (noise), raw judge output.

### 8. Backfill (re-run failures only)

**Chosen:** `--backfill latest` reads previous scores.jsonl, identifies failed/errored evals, re-runs only those.  
**Why:** A full 39-eval × 3-trial run takes ~2 hours. If 3 evals failed due to transient issues, re-running only those saves 95% of the time. Results go to a new run directory (not overwritten).

### 9. Judge prompt design

**Chosen:** Single judge prompt with generic 5-point rubric + eval-specific criteria injected.  
**Rejected:** Per-eval custom judge prompts.  
**Why:** Consistency. All evals graded on the same scale with the same rubric definitions. Eval-specific scoring anchors (PRIMARY, AUTOMATIC FAIL, Score 3/4/5) are injected via the criteria field.

### 10. What we grade (intent vs. outcome)

**Current:** We grade the agent's text response (transcript).  
**Known gap:** We don't verify tool_calls actually happened (outcome).  
**Future:** Add code-based pre-check for routing evals (did `subagent` tool get called?). This is a hybrid grading approach — code for verifiable facts, LLM for behavioral quality.

## Consequences

- Eval runs take ~2 hours for full suite (39 × 3 trials × ~60s each)
- `--trials 1 --intent-only` gives fast feedback in ~10 minutes
- Results are gitignored — they're per-run data, not source of truth
- The eval-criteria skill ensures new evals follow the same patterns
- Backfill enables cost-effective re-runs without full suite repetition

## Future Work

- [ ] Code-based pre-grading for routing evals (tool_calls verification)
- [ ] Capability vs. regression eval classification
- [ ] Negative/counter-evals (prevent over-delegation)
- [ ] Harbor adoption for containerized isolation
- [ ] Judge calibration against human scores
- [ ] Parallel execution for faster CI runs
