---
name: session-review-patterns
description: "Patterns for reviewing kiro-cli session transcripts. Use when analyzing sessions for protocol compliance, performance issues, or crew improvements."
---

# Session Review Patterns

## What to Look For

### Protocol Compliance
- Did workers emit structured DONE/BLOCKED/FAILED signals?
- Did orchestrator verify results before proceeding?
- Was verification actually run (not just claimed)?
- Were assumptions surfaced in DONE signals?

### Performance Issues
- Context overflow (agent forgets earlier instructions mid-session)
- Repeated failures without strategy change (retry amplification)
- Orchestrator doing worker work (role bleed)
- Workers asking open-ended questions instead of researching

### Crew Design Issues
- Agent prompt too long (> 80 lines = split signal)
- Skills triggering when irrelevant (vague descriptions)
- Tool/rule contradictions (allowedCommands permits what prompt forbids)
- Dead config (hooks in base crew.yaml ignored in full mode)

## Hook Gotchas

Only `agentSpawn` reliably deploys in full-mode projects (those with `crews/` directory). Other hooks (`stop`, `postToolUse`) must be defined in the themed crew YAML under the archetype, not in the base crew.yaml.

## Subagent Limitations

When spawned as subagent, these tools are NOT available:
grep, glob, code, web_search, web_fetch, use_aws, todo_list

If a session shows an agent failing because it tried to use `web_search` as a subagent — that's a crew design issue, not an agent issue.

## Red Flags in Transcripts

- "I'll try again" without changing approach → retry amplification
- Agent produces output for wrong audience → role confusion / split needed
- 3+ consecutive agent decisions without user input → rubber-stamp guard should fire
- "Done!" with no verification evidence → hallucinated success
- Agent modifies .kiro/agents/ or .kiro/steering/ → deniedPaths violation
