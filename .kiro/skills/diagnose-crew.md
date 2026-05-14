---
name: diagnose-crew
description: Diagnose agent team issues from session transcripts and feedback. Use when agents misbehave, produce poor output, or need improvement.
---

# Diagnose Crew Workflow

## Step 1: Gather Evidence

```bash
# List sessions for the project
python3 analyze-session.py --project <name>

# Get stats on a specific session
python3 analyze-session.py <session-id> --stats

# Get readable transcript
python3 analyze-session.py <session-id> --transcript > /tmp/transcript.md

# Read feedback
cat <project-path>/feedback.md

# Read current crew config
cat examples/<project>/.kiro/crew.yaml
```

## Step 2: Check for Antipatterns

### Tool Usage Patterns

| Pattern | Indicates | Fix |
|---------|-----------|-----|
| read count >> write count | Agent over-researching, under-acting | Tighten researcher scope, add "act after N reads" rule |
| shell failures > 20% | Wrong commands or missing permissions | Update allowlist, add correct commands to prompt |
| 0 subagent calls from lead | Lead doing all work itself | Strengthen "YOU DO NOT implement" boundary |
| subagent calls > 10 | Over-delegating simple tasks | Add "handle simple requests directly" to lead |
| External search > 5 per session | Missing local context | Add more to steering or resources |

### Behavioral Patterns (from transcript)

| Pattern | Indicates | Fix |
|---------|-----------|-----|
| Agent asks user questions it could research | Lazy delegation back to human | Add "research first, propose with evidence" rule |
| Reviewer suggests fixes | Role boundary violation | Add explicit "DO NOT FIX" in bold |
| Builder skips tests | Missing verification step | Add "MUST run tests before reporting done" |
| Agent repeats work already done | Context lost between turns | Check if steering/resources are loading |
| Agent uses wrong file paths | Stale or incorrect project context | Update steering with current layout |

## Step 3: Propose Specific Fixes

For each issue, write:
1. **Symptom**: What you observed (quote from transcript)
2. **Root cause**: Why it happened (missing rule, wrong permission, etc.)
3. **Fix**: Exact change to crew.yaml (before → after)

## Step 4: Apply and Verify

```bash
# Edit the crew.yaml
# Regenerate
python3 generate.py examples/<project>/.kiro/crew.yaml

# Redeploy
cp -r examples/<project>/.kiro <target-path>/.kiro

# Commit
cd <target-path> && git add .kiro/ && git commit -m "fix(agents): <what was fixed>"
```

Then test with the same task that failed before.
