---
name: adr-authoring
description: Write Architecture Decision Records when making significant technical choices. Use when selecting tools, patterns, frameworks, or making structural changes that future developers need to understand.
---

# ADR Authoring

Record decisions so future-you (and future-teammates) know WHY, not just WHAT.

## When to write an ADR

- Choosing between competing approaches (framework A vs B)
- Adopting a pattern that constrains future work
- Rejecting an obvious approach (explain why not)
- Changing a previous decision (superseding)

Do NOT write ADRs for: trivial choices, temporary experiments, or decisions that are easily reversed.

## Format (MADR-lite)

```markdown
# ADR-NNNN: [Decision Title]

**Status:** proposed | accepted | deprecated | superseded by ADR-XXXX
**Date:** YYYY-MM-DD
**Deciders:** [who was involved]

## Context

What is the issue? What forces are at play? Why does this decision need to be made now?

## Decision

What did we decide? State it clearly in one sentence, then elaborate.

## Consequences

### Positive
- [What becomes easier or better]

### Negative
- [What becomes harder or what we give up]

### Neutral
- [Side effects that aren't clearly good or bad]

## Alternatives Considered

### [Alternative 1]
- Pros: ...
- Cons: ...
- Why rejected: ...

## References

- [Research artifact that informed this] (link to docs/research/ if applicable)
- [Related ADRs]
```

## Lifecycle

1. **Proposed** — written, not yet agreed upon
2. **Accepted** — team agrees, implementation proceeds
3. **Deprecated** — no longer applies (explain why)
4. **Superseded** — replaced by a newer ADR (link to it)

## Storage

- Path: `docs/adrs/NNNN-short-title.md`
- Number sequentially (0001, 0002, ...)
- Keep an index in `docs/adrs/README.md` or link from project README

## Linking to research

If a research artifact (warlock output, BPAPPA survey) informed this decision, link it:
```
## References
- [Research: JWT vs Session Auth](../research/bpappa-auth-patterns.md) — informed this decision
```

The research artifact should back-link: `Consumed by: ADR-0003`
