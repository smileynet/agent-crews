---
name: presentation-writing
description: Create effective presentations, slide decks, and workshop materials. Use when building MARP decks, PowerPoint content, demo scripts, or any audience-facing material.
---

# Presentation Writing

Slides are not documents. A slide that requires reading has failed.

## Core Principle: Assertion-Evidence

Every slide has:
- **Headline**: A complete assertion (claim), not a topic label
- **Body**: Visual evidence supporting the assertion

Bad: "Architecture Overview"
Good: "Event-driven architecture reduces coupling between services by 60%"

The headline IS the takeaway. If someone only reads headlines, they get the full story.

## The Glance Test

Can the audience get the point in 3 seconds?
- If no → too much text, simplify
- If yes → the slide works

Rules:
- Max 6 lines of text per slide (prefer 3)
- One idea per slide
- No full sentences in bullet points (fragments are fine)
- Diagrams > tables > bullets > paragraphs

## Methodology Selection

| Talk type | Use | Why |
|-----------|-----|-----|
| Keynote / inspire | **Duarte** (story arc) | Tension between "what is" and "what could be" |
| Technical deep-dive | **Minto** (pyramid) | Lead with conclusion, support with evidence |
| Data/analytics | **Tufte** (data-dense) | Maximize information density, minimize chartjunk |
| Workshop / tutorial | **Mayer** (multimedia) | Reduce cognitive load, pair visuals with narration |
| Executive briefing | **Minto + Duarte** | Pyramid structure with emotional hook |

## MARP Support

For markdown-based decks (MARP/Marpit):

```markdown
---
marp: true
theme: default
paginate: true
---

# Assertion Headline

![bg right:40%](./assets/diagram.png)

- Evidence point 1
- Evidence point 2
- Evidence point 3

---
```

Key MARP directives:
- `<!-- _class: lead -->` — title slides
- `<!-- _backgroundColor: #1a1a2e -->` — dark slides
- `![bg right:40%](img)` — background image positioning
- `<!-- footer: 'Company © 2026' -->` — persistent footer

## Accessibility

- Alt text on every image
- Minimum 24pt font (18pt absolute minimum for notes)
- Color contrast ratio ≥ 4.5:1
- Don't rely on color alone to convey meaning
- Provide speaker notes for screen reader users

## Structure Template

1. **Hook** (1 slide) — why should they care?
2. **Context** (1-2 slides) — what's the situation?
3. **Core content** (5-15 slides) — assertions + evidence
4. **So what** (1 slide) — what should they do differently?
5. **Call to action** (1 slide) — next step

## Anti-Patterns

- ❌ Topic-label headlines ("Q3 Results") — use assertions
- ❌ Reading slides aloud — slides support speech, not replace it
- ❌ Wall of text — if it needs reading, it's a document
- ❌ Decorative images — every visual must support the assertion
- ❌ Builds/animations in markdown decks — they don't export cleanly
