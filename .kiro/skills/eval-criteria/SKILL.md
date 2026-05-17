---
name: eval-criteria
description: Style guide for writing behavioral eval criteria. Use when creating, reviewing, or modifying evals in .crews/evals.yaml to ensure reliable LLM-based grading.
---

# Eval Criteria Style Guide

Based on Anthropic's eval best practices: each eval must produce consistent scores across judge runs.

## Structure (required fields)

```yaml
- name: agent-verb-noun          # kebab-case, describes what's tested
  agent: agent-name              # must match an agent in the crew YAML
  input: "user message"          # realistic input the agent would receive
  criteria: |                    # grading rubric (see format below)
    PRIMARY: ...
    AUTOMATIC FAIL: ...
    Score N: ...
    BONUS: ...
  ideal: |                       # reference response (optional but recommended)
    What a correct response looks like.
  tags: [category, crew-name]    # for filtering (e.g., routing, scope, execution)
  threshold: 4                   # minimum passing score
```

## Criteria Format

Every criteria block follows this pattern:

```
PRIMARY: The ONE thing being tested. One sentence.
AUTOMATIC FAIL (score 1): Condition that means instant failure regardless of other qualities.
Score 3: What partial credit looks like (optional, for threshold-3 evals).
Score 4: What "good" looks like (optional, for threshold-4 evals).
BONUS (score 5): What excellence looks like beyond meeting requirements.
```

## Rules

1. **One primary signal per eval.** If you're testing two things, write two evals.
2. **Automatic-fail is mandatory.** The judge needs a clear "this is wrong" signal.
3. **Countable over subjective.** "Mentions at least 3 of: [list]" beats "describes thoroughly."
4. **Ideal responses on ambiguous evals.** Routing and execution evals MUST have ideals. Identity evals MAY omit them.
5. **Threshold matches criticality:**
   - `threshold: 4` — correctness-critical (routing, scope, safety). Wrong = broken system.
   - `threshold: 3` — quality-oriented (identity, style, narration). Partial credit acceptable.

## Anti-Patterns

| ❌ Bad | ✅ Good |
|--------|---------|
| "Should handle this correctly" | "PRIMARY: Delegates to crew-researcher" |
| "Should not do bad things" | "AUTOMATIC FAIL (score 1): Implements the feature (debugger scope is bugs only)" |
| "Should be thorough and complete" | "Score 5: mentions 5/5. Score 4: mentions 4/5. Score 3: mentions 3/5." |
| Testing routing + narration + scope in one eval | Separate eval for each concern |
| No ideal on a routing eval | Ideal showing correct delegation with brief narration |

## Tag Conventions

| Tag | What it tests |
|-----|---------------|
| routing | Correct delegation target |
| scope | Refuses out-of-scope work |
| orchestration | Correct delegation ORDER (research-first, etc.) |
| execution | Worker follows its core protocol constraint |
| identity | Agent knows its role and capabilities |
| components | Behavioral protocol activates correctly |

## Naming Convention

`{agent}-{verb}-{noun}` where:
- agent: the agent being tested (dispatcher, build-lead, etc.)
- verb: what it does (routes, refuses, checks, knows)
- noun: the target or subject (augment, invariants, workers)

Examples: `dispatcher-routes-bugfix-lead`, `augmenter-checks-invariants`, `releaser-refuses-empty-unreleased`
