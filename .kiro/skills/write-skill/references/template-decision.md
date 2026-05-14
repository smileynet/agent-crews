# Template: Decision Skill

Use for choosing between options (format selection, architecture choices, tool selection).

```markdown
---
name: skill-name
description: "Choose/select + domain. Use when [deciding between X options]."
---

# Skill Title

## Decision Flow

1. [First question to narrow options]
2. [Second question if needed]

## Selection Table

| Need / Situation | Choice | Why |
|-----------------|--------|-----|
| [condition A] | **Option 1** | [rationale] |
| [condition B] | **Option 2** | [rationale] |
| [condition C] | **Option 3** | [rationale] |

## When to switch

- [Signal that current choice is wrong → what to switch to]

## Domain specifics (read on demand)

- For [domain A]: see `references/domain-a.md`
- For [domain B]: see `references/domain-b.md`
```

## When to use this template

- Choosing between tools, formats, or approaches
- Architecture decision support
- "Which X should I use?" questions

## Key characteristics

- Decision table as the core (situation → choice → rationale)
- Questions that narrow the option space
- "When to switch" signals (you chose wrong, here's how to tell)
- Domain-specific detail lazy-linked
