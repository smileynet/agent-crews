---
inclusion: always
---

# Source Citations

When making factual claims (especially in research, reviews, and recommendations), follow these rules.

## Every claim needs a source

- Factual assertion → cite the source (URL, file path, or doc reference)
- Inference or opinion → label it: "I believe X but could not confirm — treat as tentative"
- No citing without reading — a link is not a substitute for the relevant passage

## Source hierarchy (resolve conflicts by precedence)

1. **Official documentation** — language specs, API docs, service docs
2. **RFCs, proposals, issues** — ratified design decisions
3. **Tool/library documentation** — framework-specific patterns
4. **Community consensus** — flag explicitly as "community consensus, not spec"
5. **Project conventions** — AGENTS.md, ADRs, local architecture docs

## When sources conflict

- Resolve by precedence (higher rank wins)
- If precedence doesn't resolve: surface BOTH positions with sources
- Never silently pick one

## Unverified claims

Flag them explicitly:
> "I believe X is the case but could not confirm — treat as tentative."

Do NOT omit uncertain findings. Flag and include them.
