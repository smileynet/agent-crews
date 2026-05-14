---
inclusion: always
---
# Troubleshooting Protocol

**Iron rule: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION.**

## Phase 1: Investigate
- Read the actual error (full trace, not just last line)
- Five Whys to root cause
- Call-chain tracing (where does the data flow?)
- Boundary diagnostics (which layer fails?)
- Binary search (git bisect, comment-out halves)
- Diff against last working state

## Phase 2: Pattern Analysis
- Good-vs-bad comparison (what's different?)
- Reference implementation comparison
- Evidence ladder (cheapest check first → expensive last)
- Reduction (minimal reproduction)
- Bug category triage: logic / state / environment

## Phase 3: Hypothesis
- Form ONE hypothesis with supporting evidence
- Design minimal test (change one variable)
- Predict outcome BEFORE running test
- If prediction wrong → back to Phase 1

## Phase 4: Fix
- Write failing test that captures the bug
- Apply single fix (not multiple changes)
- Verify ALL tests pass (not just the new one)
- Confirm original error is gone

## Escalation Policy
- Same approach fails 2x → STOP, change strategy entirely
- 3 different strategies fail → ask user (don't keep trying)
- Never retry the same failing approach a third time

## Red Flags (return to Phase 1 immediately)
- "Try changing this, see if it works"
- Proposing a fix before reading the error
- "I don't fully understand, but this should work"
- Retrying the same command hoping for different results
