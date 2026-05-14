# Template: Reference Skill

Use for lookup tables, schemas, and shared knowledge used across multiple skills.

```markdown
---
name: skill-name
description: "Schema/reference for [domain]. Use when [creating/modifying/debugging X]."
---

# Skill Title

## [Primary Lookup Table]

| Key | Value | Notes |
|-----|-------|-------|
| ... | ... | ... |

## [Secondary Lookup Table (if needed)]

| ... | ... |
|-----|-----|

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| [thing people get wrong] | [correct approach] |

## Troubleshooting

See `references/troubleshooting.md` for common issues and fixes.
```

## When to use this template

- API schemas, CLI flag references
- Tool name mappings, configuration options
- Shared knowledge consumed by multiple other skills
- Anything where the primary action is "look up a fact"

## Key characteristics

- Tables as the core (fast lookup, not prose)
- "Common Mistakes" section (attention anchors for known pitfalls)
- Thin process wrapper: the skill's job is to be FOUND and provide the lookup
- Troubleshooting in references/ (only loaded when something goes wrong)

## Shared knowledge pattern

When a reference skill serves multiple other skills:
- Keep it as a standalone skill (not merged into one consumer)
- Other skills can say "For X details, the agent should have the Y skill loaded"
- Or: other skills reference it inline: "See kiro-cli-schema skill for valid fields"
