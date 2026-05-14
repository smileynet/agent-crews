---
name: review-crew-quality
description: "Audit a generated crew against structural conventions. Use to check context budget, agent config, steering quality, and multi-crew consistency."
---

Audit the generated crew for `<project>` against structural quality conventions.

## Dimensions

1. **Context budget** — steering ≤150 lines total, skills ≤100 each, prompts ≤80 each
2. **Steering quality** — has build/test/lint commands, DO NOTs with alternatives, no prose overviews
3. **Skill quality** — specific triggers, actionable steps, single concern, under 100 lines
4. **Agent config** — workflow prompts (not descriptions), tool permissions match role, single responsibility
5. **Multi-crew consistency** — shared protocols, scoped availableAgents, no overlapping responsibility

## Steps

1. Read `projects/<project>/.kiro/` — measure line counts against targets
2. Check each dimension above — flag violations
3. Cross-reference: orchestrators have scope enforcement, workers have no subagent tool
4. Report findings as Must Fix / Should Fix / Looks Good

## Key Anti-Patterns

- God agent (does everything)
- Over-permissioned orchestrator (has shell/write)
- Monolithic skills (>100 lines)
- Prompt is description not workflow ("You are a researcher" vs "1. Search 2. Analyze 3. Report")
- Vague skill triggers ("help with code" vs "use when writing unit tests for React components")

## Output

```
# Crew Quality: <project>

## Context Budget
| Layer | Actual | Target | Status |

## Must Fix
1. [finding] — [fix]

## Should Fix
1. [finding] — [fix]

## Looks Good
- [what's working]
```
