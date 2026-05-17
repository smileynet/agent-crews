---
name: agents-md-authoring
description: "Write AGENTS.md files that serve as operating contracts for AI agents. Use when creating or updating AGENTS.md for a project. Trigger terms: AGENTS.md, agent instructions, agent contract, agent configuration, coding agent setup."
---

# AGENTS.md Authoring

AGENTS.md is the entry point for AI agents working in a codebase. It is not a README — it is a contract between the author and machines-with-judgment. Its job is to encode decisions an agent should not have to rediscover.

## Core Principles

1. **Agents are executors, not readers.** Every line competes for context budget. Omit what any competent agent would do by default; state only what is specific to this project.

2. **Encode done, not just started.** Verification criteria are the most important content. If the agent cannot tell whether its work is complete, it will stop too early or keep going forever.

3. **Actionable over aspirational.** "Write clean code" is noise. "No `any` types; run `npm run check` after every code change; fix all errors before committing" is a contract.

4. **Progressive disclosure.** Inline what's frequently needed; reference what's rarely needed. Link to `.docs/` files with a one-line description of *when* to read them.

## Recommended Structure

```markdown
# AGENTS.md

## Project
<!-- 2-4 sentences: what it does, primary focus, non-obvious terminology -->

## Architecture
<!-- Key directories, package boundaries, how pieces connect -->

## Commands
<!-- Exact commands. Not "run the tests" — the actual invocation. -->
<!-- Include: what to run after code changes, what is FORBIDDEN -->

## Code Standards
<!-- Language-specific rules that deviate from defaults -->
<!-- Only rules that are enforced — aspirational conventions erode trust -->

## Workflow
<!-- When to ask vs proceed, commit/push rules, session completion -->

## Testing
<!-- Framework, how to run specific tests, what to do after modifying tests -->

## Verifying Work
<!-- What "done" means. Exact commands, expected output, what failure looks like. -->

## References
<!-- Links to .docs/ files with WHEN to read them -->
```

## Size Guidelines

Effective range: 100-300 lines. The 530-line ceiling works only for large monorepos where every line is load-bearing.

**Heuristic:** If the agent needs it on any non-trivial task → inline. If only for a specific task class → link to `.docs/`. If the agent wouldn't need it → delete.

## Audience Separation

| File | Audience | Content |
|------|----------|---------|
| README.md | Humans | Project purpose, setup, usage |
| AGENTS.md | AI agents | Operating contract, commands, verification |

Never duplicate between them. Content written for one should not appear in the other.

## Anti-Patterns

- **Too long** — 500 lines of background context the agent rarely needs. Front-load high-frequency content.
- **Too vague** — "Follow good engineering practices" produces vague behavior.
- **Duplicating README** — wastes context and creates maintenance fork.
- **No verification criteria** — agent cannot tell if output is acceptable.
- **Aspirational conventions not enforced by tooling** — teaches agent to claim compliance without evidence.
- **Stale autonomy directives** — blanket "never ask" left from a different task type.

## Sources

- best_practices/docs/practices/agents-md-authoring.md (internal)
- Observed across 10+ real AGENTS.md files: 84-530 lines effective range
