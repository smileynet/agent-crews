---
name: spike-workflow
description: "Workflow for technical spikes — standalone experiments that prove or disprove assumptions. Use when building benchmarks, testing integrations, or validating architecture decisions before committing to an approach."
---

# Spike Workflow

## Spike vs Production Code

Spikes are EXPERIMENTS, not features. They:
- Live in a scratch/spike directory (standalone, not integrated)
- Measure feasibility, not correctness
- Have explicit pass/fail criteria defined BEFORE coding
- Are disposable — learnings transfer, code may not

## Process

1. **Define hypothesis**: "We can do X within constraint Y"
2. **Set pass/fail criteria**: specific, measurable numbers
3. **Build minimal proof**: strip everything not needed to test the hypothesis
4. **Run and measure**: record actual results
5. **Decision**: proceed, pivot, or investigate further

## Rules

- No production polish (error handling, logging, CI)
- One hypothesis per spike
- Time-box: if you can't prove it in a day, narrow the hypothesis
- Record results even if FAIL — negative results are valuable
- Graduate learnings to ADRs or specs, not the code itself
