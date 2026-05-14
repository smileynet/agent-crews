---
name: analyze-sessions
description: Guide users through session analysis and crew improvement. Help them identify issues, interpret patterns, and decide on fixes.
---

# Session Analysis — Advisory Guide

## When a user wants to analyze a session

Ask:
- Was there a specific session that felt off, or are you doing a general health check?
- What project? (needed to filter sessions)
- What went wrong? (helps focus the analysis)

## Running analysis

```bash
# List sessions for a project
uv run analyze-session.py --project <path>

# Stats (tool usage, agent calls, timing)
uv run analyze-session.py <session-id> --stats

# Readable transcript
uv run analyze-session.py <session-id> --transcript

# Behavioral compliance check
uv run analyze-session.py <session-id> --compliance

# Anti-pattern detection
uv run analyze-session.py <session-id> --antipatterns
```

## Interpreting results

### Tool usage patterns to flag

| Pattern | Question to ask user |
|---------|---------------------|
| Read count >> write count | "Was the agent researching too long before acting?" |
| Shell failures > 20% | "Are the right commands in the allowlist?" |
| Zero subagent calls from lead | "Was the lead doing everything itself?" |
| Many web searches | "Is there local context missing from steering?" |
| Repeated file reads (same file) | "Agent may be losing context between turns" |

### Behavioral issues to surface

| Issue | Likely cause | Fix direction |
|-------|-------------|---------------|
| Wrong routing | Dispatcher scope/handles mismatch | Edit crew YAML scope section |
| Agent does out-of-scope work | Missing or weak refuses list | Add explicit refuses |
| Skips verification | Component not loading or commands null | Check fleet.yaml verification config |
| Doesn't commit | Git component variant or missing remote | Check git config |
| Over-delegates | Lead threshold too low | Add "handle simple requests directly" |
| Under-delegates | Lead doing worker tasks | Strengthen "DO NOT implement" boundary |

## Guiding the improvement loop

After identifying issues, help the user decide:
1. Is this a crew YAML fix (routing, scope, delegation rules)?
2. Is this a component fix (behavioral rule needs tuning)?
3. Is this a steering fix (project context is stale or missing)?
4. Is this a skill gap (agent needs knowledge it doesn't have)?

Then:
- Make the edit
- `just build` to regenerate
- `just link <project>` to redeploy
- Test with the same task that failed
- Optionally write an eval to prevent regression

## When to suggest @tune-crew

If the user has multiple sessions with recurring issues, suggest the full tuning loop (`@tune-crew`) rather than one-off fixes. It's more systematic: analyze → diagnose → fix → validate.
