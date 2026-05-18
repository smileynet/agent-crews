# ADR-005: Skill Design Principles

**Date:** 2026-05-14
**Status:** Accepted
**Context:** Thunderdome audit of 28 skills revealed inconsistent structure, context budget waste, and unclear boundaries. This ADR captures the principles that guided cuts, merges, and restructuring — and should guide future skill reviews.

## Decisions

### 1. SKILL.md = process, references/ = context

SKILL.md contains what the agent should DO (steps, templates, decision tables). Reference files contain what the agent needs to KNOW (examples, lookup data, checklists). Mixing them degrades both — the agent can't distinguish instructions from background.

**Source:** MindStudio research, kiro.dev docs, Claude Code skills architecture consensus.

### 2. Templates direct attention, not teach knowledge

Even if an LLM "knows" something, a template anchors what to prioritize in this context. Cutting a pattern because "the LLM already knows it" is wrong — the skill's job is to focus attention, not educate.

**Implication:** Keep concise attention anchors (signal → fix tables) even for well-known patterns. Cut verbose explanations of WHY.

### 3. Anti-patterns live with their skill, not standalone

A standalone "antipatterns" skill has no clear trigger and loads generic content regardless of task. Anti-patterns are the "what NOT to do" complement of a specific skill's "what TO do."

**Applied:** Dissolved `antipatterns.md` → code antipatterns into `coding-principles.md`, review antipatterns into `code-review.md`.

### 4. Domain-specific content uses lazy linking

Universal principles stay in SKILL.md. Stack-specific examples go in `references/` and load only when the agent identifies the relevant domain. This provides contextual specificity without context bloat.

**Pattern:** "For TypeScript projects, read `references/examples-typescript.md`"

### 5. Troubleshooting is a section within executable skills

Skills that involve commands/tools/generation include a troubleshooting section (symptom → cause → fix). Advisory skills (decision trees, style guides) don't need one. If troubleshooting exceeds ~20 lines, extract to `references/troubleshooting.md`.

**Structure:** Symptom-indexed, copy-pasteable fixes, expected output shown, escalation path.

### 6. Four skill types with distinct templates

| Type | Core structure | Troubleshooting? |
|------|---------------|:----------------:|
| Process | Numbered steps, verification | Yes |
| Decision | Selection table, "when to switch" signals | No |
| Reference | Lookup tables, common mistakes | No |
| Review | Ordered dimensions, severity, anti-pattern anchors | If checks run commands |

### 7. Skills under 100 lines, no exceptions without justification

Context budget is finite. Every line loaded costs every turn. Skills over 100 lines must either be split (multi-file) or justify why the content can't be reduced.

### 8. Shared knowledge stays as standalone reference skills

When a reference skill serves multiple other skills (e.g., kiro-cli-schema used by kiro-helper AND crew-creator), keep it standalone. Don't merge it into one consumer — that breaks the other consumers.

### 9. Cut criteria (what earns removal)

| Signal | Verdict |
|--------|---------|
| Unreferenced by any crew or agent | CUT (unless wiring bug — fix the reference) |
| Project-specific (one user's stack) | CUT from shared, user adds to their project |
| Duplicates content in another skill | MERGE into the canonical home |
| Purely explanatory (no actionable instructions) | REWRITE as templates/steps or CUT |
| Over 100 lines with extractable domain content | SPLIT into multi-file |

### 10. Keep criteria (what earns its place)

| Signal | Verdict |
|--------|---------|
| Referenced by crews/agents (actively loaded) | KEEP |
| Provides attention anchors for known-but-skippable patterns | KEEP |
| Serves as shared knowledge across multiple skills | KEEP as standalone reference |
| Under 100 lines, clear trigger, actionable content | KEEP |

## Alternatives Rejected

- **"LLMs know this, cut it"** — Wrong framing. Skills focus attention, not teach. Rejected.
- **Mandatory troubleshooting in all skills** — Advisory skills can't fail. Only executable skills need it.
- **Single monolithic skill template** — Different skill types serve different purposes. Four templates.
- **Inline all domain examples** — Burns context for irrelevant stacks. Lazy linking is better.

## Consequences

- Future skill reviews use this ADR as the rubric
- New skills must identify their type and use the corresponding template
- Skills over 100 lines trigger automatic review for multi-file extraction
- The write-skill skill (`.kiro/skills/write-skill/`) is the living reference implementation
