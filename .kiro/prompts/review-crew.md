---
description: "Cross-session crew performance review — analyze patterns, identify improvements"
---
# Review Crew

Review agent team performance across sessions to identify improvements for both the project-local crew and the agent-crews repo.

## Parameters

- `project` (required): Project name (e.g., `my-project`)
- `scope` (optional): `local` (project crew only), `general` (also propose agent-crews improvements), or `both` (default)

## Steps

### Gather Data

1. MUST list all sessions: `python3 analyze-session.py --project <project>`
2. MUST run `--stats` on the 3-5 most recent sessions
3. MUST read `<project-path>/feedback.md` for user observations
4. MUST read `<project-path>/scratch/progress.md` for lead's self-reported progress
5. SHOULD read git log in target project for what was actually delivered: `git -C <path> log --oneline --since="1 week ago"`

### Analyze Patterns Across Sessions

6. MUST compare tool usage across sessions — are patterns improving or repeating?
7. MUST check: are the same issues appearing in feedback.md repeatedly? (unresolved systemic issue)
8. MUST check: is the turns-per-prompt ratio improving? (agent getting more autonomous)
9. MUST check: are subagent delegations effective? (work completed vs bounced back)
10. SHOULD read 1-2 transcripts for qualitative issues (tone, over-explaining, wrong assumptions)

### Identify Improvements

11. MUST categorize findings as:
    - **Project-local fix**: Change this project's crew.yaml, steering, or skills
    - **General improvement**: Change base base, shared skills, or generate.py
    - **New pattern**: Document in docs/decisions/patterns.md

12. MUST prioritize by impact:
    - 🔴 Blocking: Agent can't complete tasks (wrong commands, missing permissions)
    - 🟡 Friction: Agent completes but inefficiently (over-researching, poor delegation)
    - 🟢 Polish: Agent works but output quality could improve (formatting, conventions)

### Propose Changes

13. MUST write specific proposals with before/after for crew.yaml changes
14. MUST note which proposals are local vs general
15. SHOULD propose new skills if a pattern repeats across 2+ sessions
16. MAY propose new antipatterns for docs/decisions/patterns.md

## Output

```markdown
# Crew Review: <project>

## Sessions Analyzed
- <id>: <summary>

## Issues (🔴 Blocking > 🟡 Friction > 🟢 Polish)
1. [issue] — evidence — fix

## Proposed Changes (project-local vs general)
- [ ] [change]
```
