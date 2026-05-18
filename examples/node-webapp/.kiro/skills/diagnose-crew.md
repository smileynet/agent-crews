---
name: diagnose-crew
description: Guide users through diagnosing agent issues. Ask about symptoms, help identify root causes, suggest targeted fixes.
---

# Diagnose Crew — Advisory Guide

## When a user reports agent issues

Ask:
- What did the agent do wrong? (specific behavior, not just "it's broken")
- Which agent? (dispatcher, a lead, a worker?)
- Was this a one-time thing or recurring?
- Can you point me to the session? (session ID or project path)

## Diagnosis approach

### 1. Gather evidence

```bash
uv run analyze-session.py <session-id> --stats
uv run analyze-session.py <session-id> --antipatterns
```

Read the transcript if stats aren't conclusive:
```bash
uv run analyze-session.py <session-id> --transcript
```

### 2. Match symptoms to causes

| Symptom | Likely cause | Where to look |
|---------|-------------|---------------|
| Routes to wrong agent | Scope overlap or missing handles | Crew YAML `scope.handles` |
| Agent does work outside its role | Missing refuses or weak boundary | Crew YAML `scope.refuses` + agent prompt |
| Lead does everything itself | Delegation rules too weak | Lead prompt — "DO NOT implement" section |
| Agent asks user obvious questions | Missing "research first" rule | Agent prompt or steering |
| Skips tests/verification | Verification component not configured | .crews/crew.yaml `verification.checks` |
| Doesn't commit | Git component or no remote | .crews/crew.yaml `git.variant` |
| Ignores project conventions | Stale `AGENTS.md` | Owner-managed `AGENTS.md` at project root |
| Uses wrong file paths | Project layout changed | Update steering with current structure |

### 3. Propose fixes

For each issue, surface:
- **What you observed** (quote or describe specific behavior)
- **Why it happened** (which config/rule is missing or wrong)
- **What to change** (specific file + specific edit)

Ask: "Does this match what you experienced? Should I apply this fix?"

## Key considerations to surface

- One fix at a time — changing multiple things obscures what helped
- After fixing, test with the same task that failed
- Consider writing an eval to catch regressions
- If the same issue recurs across sessions, it's a structural problem (component or crew design), not a one-off

## After fixing

Remind:
1. `just build <project>` to regenerate and redeploy
3. Test with the original failing task
4. Optionally: `just eval` to verify no regressions

## Structural audit (when the user asks "is this crew well-built?")

Some diagnoses are not about a failing behavior but about structural quality. When
the user wants an audit of the *shape* of a deployed crew rather than a specific
bug, walk these dimensions:

1. **Context budget** — steering ≤150 lines total, skills ≤100 each, prompts ≤80
   each. Inflated context burns tokens for no benefit.
2. **Steering quality** — has build/test/lint commands, DO NOTs with alternatives,
   no prose overviews disguised as steering.
3. **Skill quality** — specific triggers, actionable steps, single concern, under
   100 lines.
4. **Agent config** — workflow prompts (not descriptions), tool permissions match
   role, single responsibility per agent.
5. **Multi-crew consistency** — shared protocols, scoped `availableAgents`, no
   overlapping responsibility between crews.

### Common anti-patterns

- God agent (does everything)
- Over-permissioned orchestrator (has shell/write)
- Monolithic skills (>100 lines)
- Prompt is description not workflow ("You are a researcher" vs "1. Search 2.
  Analyze 3. Report")
- Vague skill triggers ("help with code" vs "use when writing unit tests for React
  components")

### Report shape

Classify each finding as **Must fix** / **Should fix** / **Looks good**. Quote
the offending file/line; propose the specific edit.
