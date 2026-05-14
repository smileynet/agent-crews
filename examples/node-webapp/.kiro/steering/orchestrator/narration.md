---
inclusion: always
---
# Narration Protocol (Verified)

## When to Narrate
- **Before delegating:** announce plan (what, who, why)
- **Between steps:** one-line status update
- **After completion:** summary with evidence

## Grounding: VERIFIED
Before reporting DONE, dispatch the verifier subagent.
- Verifier sees: original task + final output/state
- Verifier does NOT see: your reasoning or conversation history
- Verifier returns: PASS (with what was confirmed) or FAIL (with specific gaps)

If verifier returns FAIL: address gaps before reporting DONE.

## When Verified Applies
Use verified grounding for any task that produces artifacts which could be wrong:
- Code changes, config changes, infrastructure modifications
- Documents with factual claims
- Any deliverable the user will rely on
