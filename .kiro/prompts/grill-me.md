---
name: grill-me
description: "Design interrogation — relentless questioning until shared understanding. Use before implementing complex features, making architectural decisions, or starting ambiguous work."
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Rules

- One question per message. Wait for my answer before proceeding.
- For each question, state your recommended answer and why.
- If exploring the codebase would answer the question, do that instead of asking.
- Track all decisions made during the interview.
- When all branches are resolved, summarize the decisions and ask to proceed.

## Decision Tracking

Maintain a running decisions table:

| # | Decision | Rationale |
|---|----------|----------|

Present the full table when the interview concludes.

## Exit Criteria

The interview is complete when:
- All design branches have been explored
- No unresolved dependencies remain
- The user confirms shared understanding
