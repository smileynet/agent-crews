# Review Session

Analyze a kiro-cli session to identify improvements for an agent team.

## Parameters

- `project` (required): Project name to filter sessions (e.g., `<project>`)
- `session_id` (optional): Specific session ID. If omitted, analyzes the most recent.

## Steps

1. MUST run `python3 analyze-session.py --project <project>` to list sessions
2. MUST run `python3 analyze-session.py <id> --stats` for tool usage patterns
3. MUST run `python3 analyze-session.py <id> --transcript` and read the flow
4. SHOULD read `<project-path>/feedback.md` for user observations
5. MUST identify antipatterns (reference `.kiro/skills/diagnose-crew.md`)
6. MUST propose specific fixes with before/after for crew.yaml
7. SHOULD ask user which fixes to apply
8. MAY apply fixes, regenerate, and redeploy if user approves

## Output

Summary with:
- Session stats (tool calls, turns ratio, delegation count)
- Issues identified (with evidence from transcript)
- Proposed fixes (specific crew.yaml changes)
