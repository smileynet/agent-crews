---
name: ai-assisted-development
description: Principles for effective AI-assisted development. Use when generating code with AI, reviewing AI output, or structuring work for agent collaboration.
---

# AI-Assisted Development

## Workflow

1. **Decompose** — break into independently solvable units
2. **Specify** — write tests or acceptance criteria BEFORE generating
3. **Generate** — let AI produce implementations
4. **Verify** — run tests, check types, review architectural fit
5. **Integrate** — compose verified units, test at boundaries

## Rules

- You own the output. AI authorship doesn't transfer quality obligations.
- Write tests first — they give AI unambiguous success criteria.
- Small functions = small blast radius when wrong.
- Review against INTENT, not just correctness. AI satisfies the letter while violating the spirit.
- Keep modules small enough for one human to reason about independently.

## Before Accepting AI Output

- [ ] Tests pass (not just "looks right")
- [ ] Types check (catches interface mismatches)
- [ ] Boundaries reviewed (does it respect module contracts?)
- [ ] Error paths exist (AI defaults to happy-path only)
- [ ] No mystery code (if you can't explain why it works, don't ship it)

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Accepting without running tests | Always verify before integrating |
| Generating entire systems at once | Decompose into testable units |
| Trusting AI's "this should work" | Run it. Read the output. |
| Accumulating code nobody understands | Document WHY in ADRs, keep modules small |
