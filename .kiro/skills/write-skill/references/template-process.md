# Template: Process Skill

Use for step-by-step workflows (deploy, review, create, migrate).

```markdown
---
name: skill-name
description: "Verb + object + context. Use when [specific trigger]."
---

# Skill Title

## Steps

1. [First action — explicit, executable]
2. [Second action — reference files if needed: `references/checklist.md`]
3. [Third action — conditional: "If X, read `references/x-guide.md`"]
4. [Verification step — how to confirm it worked]

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| [what you observe / error text] | [why] | [exact action] |
| [another failure mode] | [why] | [exact action] |

If not resolved: [escalation — what to try next or who to ask]

## Rules

- [Constraint 1]
- [Constraint 2]

## Anti-Patterns

- [What NOT to do + why]
```

## When to use this template

- Deploying something
- Creating/generating artifacts
- Migration/upgrade procedures
- Any repeatable multi-step workflow

## Key characteristics

- Numbered steps (order matters)
- Each step is executable (not "consider" or "think about")
- Verification at the end
- Troubleshooting section: symptom-indexed, for self-recovery when steps fail
- References loaded conditionally mid-process

## Troubleshooting section guidelines

Include when the skill involves commands, tools, or external systems that can fail.
Omit for purely advisory skills (decision trees, style guides).

Structure:
- **Symptom-indexed**: reader searches by what they SEE (error message, unexpected output)
- **Expected output**: show what success looks like so failure is obvious
- **Copy-pasteable fixes**: exact commands, not "try adjusting the config"
- **Escalation path**: when to stop self-recovering and ask the user
