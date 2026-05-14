# Session Analysis

Understand how your agents actually perform by analyzing session transcripts.

## Why analyze sessions

Agents don't always behave the way you designed them to. Session analysis reveals:
- **Routing failures** — dispatcher sending work to the wrong agent
- **Scope violations** — agents doing work outside their role
- **Protocol gaps** — agents skipping verification, not committing, ignoring rules
- **Efficiency issues** — over-researching, excessive tool calls, repeated failures

## When to analyze

- After a session that felt off (agent was slow, wrong, or unhelpful)
- Periodically to check crew health (weekly or after major crew changes)
- Before tuning — understand current behavior before changing it
- After deploying crew updates — verify improvements landed

## Running analysis

```bash
# List recent sessions
uv run analyze-session.py

# Sessions for a specific project
uv run analyze-session.py --project ~/code/my-project

# Analyze a specific session
uv run analyze-session.py <session-id> --stats

# Get readable transcript
uv run analyze-session.py <session-id> --transcript

# Check behavioral compliance
uv run analyze-session.py <session-id> --compliance

# Detect anti-patterns
uv run analyze-session.py <session-id> --antipatterns
```

## What to look for

### Tool usage patterns

| Pattern | Might mean |
|---------|-----------|
| Many reads, few writes | Agent over-researching, not acting |
| High shell failure rate | Wrong commands or missing permissions |
| Zero subagent calls from lead | Lead doing all work itself |
| Excessive subagent calls | Over-delegating trivial tasks |
| Many web searches | Missing local context in steering |

### Behavioral signals

| Signal | Might mean |
|--------|-----------|
| Agent asks user what it could research | Missing "research first" rule |
| Reviewer writes code | Role boundary violation |
| Builder skips tests | Verification component not loading |
| Agent repeats completed work | Context loss between turns |

## The improvement loop

1. **Observe** — analyze sessions, identify patterns
2. **Diagnose** — determine root cause (missing rule, wrong scope, bad routing)
3. **Fix** — edit crew YAML or component
4. **Regenerate** — `just build` + `just link`
5. **Verify** — run the same task again, or run evals

Use `@tune-crew` to have agents walk you through this loop.
