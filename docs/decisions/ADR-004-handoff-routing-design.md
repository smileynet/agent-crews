# ADR-004: Handoff and Routing Design

**Status:** Accepted  
**Date:** 2026-05-12

## Context

Designed the handoff and routing system for multi-crew projects. Needed to define how orchestrators discover sibling crews, suggest handoffs to users, and enforce scope boundaries.

## Decisions

### Cross-Crew Handoff

1. **Handoffs are user-mediated suggestions only.** Orchestrators suggest switching, never dispatch cross-crew. Prevents runaway token spend, keeps user as session owner.
2. **Add `scope.description` field.** One-line natural language summary per crew, used in handoff prompt text. `scope.handles` stays for programmatic matching.
3. **Each crew defines its own copy of shared agents (committer, verifier).** Keeps crews self-contained, no cross-crew dependencies.
4. **Handoff suggestions include context summary.** Orchestrator provides 2–3 sentence context the user can paste if starting a fresh session.

### Scope Enforcement

5. **`scope.refuses` used for both build-time validation and runtime prompt reinforcement.** Coverage gap warnings at build time; "Do NOT attempt" injected into orchestrator prompts at runtime.
6. **Visual format distinction.** Table for intra-crew routing (dispatch), list for cross-crew handoff (suggest). Reinforces behavioral difference.
7. **Handoff entries ordered by relevance.** Siblings whose `handles` overlap with this crew's `refuses` come first, then alphabetical.

### Intra-Crew Routing

8. **`routes:` stays free-text for worker agents.** Natural language works better in prompts than structured keywords at agent level.
9. **Workers escalate to their own orchestrator only.** Never make routing decisions, never suggest handoffs to user.

### Feedback

10. **No automated feedback loop.** Manual tuning via crew-analyst is sufficient. Revisit if >10% handoff failure rate observed.

## Implementation

- `scope.description` used in generated handoff text (falls back to comma-joined handles)
- `scope.refuses` injected as "Do NOT attempt" in orchestrator prompts
- Ordering uses set intersection of refuses ∩ sibling handles
- Coverage validation warns at build time if refused scopes have no covering crew
- Worker archetype prompts include escalation instruction
