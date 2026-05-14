---
inclusion: always
---

# Available Specialist Agents

When the user's request matches a specialist, delegate via the `subagent` tool rather than doing it yourself.

| Request pattern | Delegate to | Role |
|----------------|-------------|------|
| "Research..." / "Investigate..." / "What does best_practices say..." / "Consider..." / "Survey..." | crew-researcher | Deep investigation — patterns, prior art, best practices |
| "Create a crew for..." / "Build agents for..." | crew-creator | Builds crews for new projects |
| "Add an agent..." / "Add a feature to the crew..." / "Upgrade [agent]..." | crew-augmenter | Researches + implements new agents/features |
| "Fix [agent issue]..." / "Why isn't [agent] working..." | crew-doctor | Diagnoses and fixes crew problems |
| "Analyze sessions..." / "Review performance..." / "Check protocol compliance..." | crew-analyst | Analyzes session transcripts for improvements |
| "Tune the crew..." / "Review and fix agent issues..." | crew-analyst → crew-augmenter | Observe → diagnose → fix loop (use @tune-crew prompt) |

When a build/modify task needs context first, delegate to crew-researcher BEFORE the implementing agent.

Delegate the FULL task — don't do partial work then hand off.
