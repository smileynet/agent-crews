---
inclusion: always
---
# Decision Protocol (Progressive Formalization)

## Capture → Log → ADR Pipeline

### Level 1: Capture (always)
Every decision goes in the assumption register. No ceremony needed.
- "We chose X because Y"
- "Assumed Z — not confirmed"

### Level 2: Log (significant decisions)
When a decision is significant, persist to decision log:
- What was decided
- What alternatives were considered
- Why this option won
- What context informed it

### Level 3: ADR (when signals present)
Promote to Architecture Decision Record when:
- Constrains future work (can't easily reverse)
- Required research to decide
- Affects multiple components or teams
- Has been explained twice (sign it needs documentation)

## Nudge, Don't Enforce
- Never block work for missing formality
- Suggest promotion when signals appear: "This decision might warrant an ADR because..."
- User can decline — that's fine
- Better to capture informally than not at all

## Spec Process (Available, Never Mandatory)
For complex work, offer to draft a lightweight spec:
- Problem statement
- Key scenarios (3-5)
- Requirements (must/should/could)
- Assumptions
- Success criteria

Never gate work on spec completion. Offer it as a tool, not a gate.
