# Template: Review Skill

Use for evaluating, auditing, or checking something against criteria.

```markdown
---
name: skill-name
description: "Review/audit [what]. Use when [evaluating X for quality/compliance/issues]."
---

# Skill Title

## Dimensions (check in this order)

1. **[Dimension A]** — [what to check, pass/fail criteria]
2. **[Dimension B]** — [what to check, pass/fail criteria]
3. **[Dimension C]** — [what to check, pass/fail criteria]

## Severity

| Level | Meaning | Action |
|-------|---------|--------|
| BLOCKING | [definition] | Must fix |
| WARNING | [definition] | Should fix |
| INFO | [definition] | Nice to fix |

## Anti-Patterns (flag these)

| Signal | Issue |
|--------|-------|
| [observable symptom] | [what's wrong] |

## Output

Report findings as: [severity] [finding] — [fix]
```

## When to use this template

- Code review, doc review, architecture review
- Compliance/quality audits
- Health checks and validation passes

## Key characteristics

- Ordered dimensions (check priority)
- Severity classification (triage findings)
- Anti-patterns as attention anchors (what to actively look for)
- Troubleshooting section if checks involve commands that can fail
- Minimal output spec (don't over-prescribe format)
