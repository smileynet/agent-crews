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
| Skips tests/verification | Verification component not configured | fleet.yaml `verification.checks` |
| Doesn't commit | Git component or no remote | fleet.yaml `git.variant` |
| Ignores project conventions | Stale project.md steering | `.kiro/steering/project.md` |
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
1. `just build` to regenerate
2. `just link <project>` to redeploy
3. Test with the original failing task
4. Optionally: `just eval` to verify no regressions
