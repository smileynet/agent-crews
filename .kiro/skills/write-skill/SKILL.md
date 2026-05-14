---
name: write-skill
description: Create or restructure skills for agent crews. Use when creating a new skill, splitting a skill that's too large, or converting a single-file skill to multi-file.
---

# Writing Skills

## Process

1. Determine the skill type (see below)
2. Choose single-file or multi-file based on size/domain variance
3. Write SKILL.md using the appropriate template from `references/`
4. Set the `description` as a specific trigger (keywords + "Use when...")
5. Add to agent's `resources` in crew.yaml
6. Run `just build`

## Skill Types

| Type | Purpose | Template |
|------|---------|----------|
| **Process** | Step-by-step workflow | `references/template-process.md` |
| **Decision** | Choose between options | `references/template-decision.md` |
| **Reference** | Lookup tables, schemas | `references/template-reference.md` |
| **Review** | Evaluate/audit something | `references/template-review.md` |

## Single-File vs Multi-File

**Single-file** (`shared/skills/my-skill.md`): Universal, under 100 lines, no domain variants.

**Multi-file** (`shared/skills/my-skill/`):
```
my-skill/
├── SKILL.md              # Core (≤100 lines, loaded on trigger)
└── references/           # On-demand (agent reads when instructed)
    ├── examples-*.md     # Domain-specific examples
    └── checklist.md      # Verification/audit lists
```

## Rules

- SKILL.md = process (what to DO). References = context (what to KNOW).
- Description is the trigger — specific keywords, not vague topics
- Templates direct attention — even for "known" things, they anchor priority
- Anti-patterns live WITH their skill, not standalone
- Troubleshooting lives IN the skill (symptom→fix table) for executable skills — not as a separate file
- Explicit file loading: "Read `references/checklist.md`" — never assume agent finds files
- Conditional loading by domain: "If Rust project, read `references/examples-rust.md`"
- Reference skills that serve multiple other skills → keep as standalone lookup (thin SKILL.md + fat references/)

## Anti-Patterns

- SKILL.md as knowledge dump (mix of process + encyclopedia)
- Vague triggers ("help with code")
- Output templates longer than instructions
- Stack-specific boilerplate inline instead of in references/
- Standalone "anti-patterns" skill instead of integrating with the relevant skill
