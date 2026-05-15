# ADR-006: High Reliability as Design Principle

**Status:** Accepted
**Date:** 2026-05-15

## Context

agent-crews is a published tool that generates and deploys AI agent teams to coding projects. The quality of generated crews directly impacts every project that uses them. A subtle bug in a crew definition, a missed validation, or a poorly-written changelog entry compounds across all deployments.

We observed that prompt-only restrictions are routinely ignored by agents (proven by eval: steering-based delegation rules had 0% effect). Only structural enforcement (tool removal, automated validation, gated pipelines) reliably produces correct behavior.

## Decision

**High reliability is the core value proposition of agent-crews.** Every design decision favors reliability over speed.

This means:

1. **Enforcement over suggestion.** If something must happen, make it structurally impossible to skip. Tool permissions enforce; prompts suggest (ADR-001 #3).
2. **Validation is automatic, not optional.** Every change flows through crew-validator. The augmenter → validator pipeline is the default, not an opt-in.
3. **Eval coverage for behavioral changes.** When agent behavior is modified, affected evals must be updated or re-run. crew-validator recommends this.
4. **Changelog discipline is enforced.** User-facing changes require changelog entries. The verifier checks; the release script blocks on empty.
5. **Generated output is verified.** `just build` must pass before any change is considered complete. Drift between source and output is a blocking issue.

## Alternatives Considered

- **Move fast, fix later.** Rejected — crew bugs compound across all deployed projects. A broken crew definition affects every session until fixed.
- **Trust agent judgment.** Rejected — eval data shows agents ignore soft constraints. Only structural enforcement works reliably.
- **Manual review only.** Rejected — doesn't scale. Automated validation catches what humans miss.

## Consequences

- New agents: crew-validator (post-change verification), crew-releaser (release pipeline)
- Auto-chain pattern: augmenter → validator is the default pipeline
- Eval framework is a first-class concern, not an afterthought
- Changelog component enforces entry quality at the verifier level
- Slower individual changes, but fewer regressions and higher trust in releases
