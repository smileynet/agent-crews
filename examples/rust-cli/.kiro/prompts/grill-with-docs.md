---
name: grill-with-docs
description: "Design interrogation that updates domain docs inline. Use when stress-testing a plan against your project's language, glossary, and documented decisions."
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

Ask one question at a time. Wait for my answer before continuing.

For each question:
- Provide 2-4 relevant answers.
- Give the rationale and tradeoffs for each answer.
- Recommend one answer and say why.

Question discipline:
- Ask me only about decisions that are genuinely product-defining, user-facing, or meaningfully irreversible.
- If the repo, docs, or code can answer something, explore and answer it yourself instead of asking.
- Do not ask me to choose implementation details, file layouts, naming minutiae, or mechanics unless multiple clean options remain after exploration and the choice materially affects the mental model or public API.
- Prefer deriving lower-level decisions from already-resolved principles instead of escalating them as questions.

## Domain Awareness

Look for existing documentation:

- `CONTEXT.md` at repo root (glossary of domain terms)
- `docs/adr/` (architectural decision records)

If neither exists, create them lazily when the first term or decision is resolved.

## During the Session

### Challenge against the glossary
When I use a term that conflicts with `CONTEXT.md`, call it out: "Your glossary defines 'X' as Y, but you seem to mean Z — which is it?"

### Sharpen fuzzy language
When I use vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean Customer or User?"

### Discuss concrete scenarios
Stress-test domain relationships and UX with concrete scenarios that probe edge cases, lifecycle boundaries, and ownership boundaries.

### Cross-reference with code
When I state how something works, check whether the code agrees. Surface contradictions.

### Update CONTEXT.md inline
When a term is resolved, update `CONTEXT.md` immediately. Don't batch. Format:

```md
**Term**:
One-sentence definition.
_Avoid_: synonym1, synonym2
```

CONTEXT.md is a glossary only — no implementation details, no specs, no scratch notes. Include any term relevant to the project that could cause confusion — domain concepts, infrastructure conventions, and internal naming decisions all belong.

### Offer ADRs sparingly
Only create an ADR when ALL THREE are true:
1. **Hard to reverse** — changing later is expensive
2. **Surprising without context** — a future reader would wonder why
3. **Real trade-off** — genuine alternatives existed

ADR format: `docs/adr/NNNN-slug.md` with a short title and 1-3 sentence explanation of context + decision + why. Keep it minimal.

## Exit Criteria

The interview is complete when:
- All design branches explored
- No unresolved dependencies
- `CONTEXT.md` updated with any new/changed terms
- ADRs written for qualifying decisions
- I confirm shared understanding
