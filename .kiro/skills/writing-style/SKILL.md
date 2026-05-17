---
name: writing-style
description: "Writing style for technical documentation, README files, guides, and any user-facing text. Use when writing or reviewing prose, docs, comments, commit messages, or PR descriptions. Trigger terms: writing, prose, documentation style, tone, clarity, technical writing."
---

# Writing Style

Every sentence earns its place. Cut until cutting would lose meaning.

## Required Patterns

**Answer-first.** Lead with the conclusion. The reader gets value from sentence one.
- Bad: "There are several factors to consider... Taking all of this into account, PostgreSQL is probably your best bet."
- Good: "Use PostgreSQL. It handles your read-heavy workload and your team knows it."

**Impact over mechanism.** State what changed or what the reader should know — not how the code does it.
- Bad: "Refactored `process_queue` to use a deque instead of a list and updated the sentinel from -1 to None."
- Good: "Fixed queue processing to handle concurrent inserts without dropping items."

**Specific words.** Name the thing. "The deploy failed because the config references a deleted secret" — not "There was an issue with the deployment process."

**Active voice.** "The script deletes old logs" — not "Old logs are deleted by the script." Passive only when the actor is unknown or irrelevant.

**Proportional depth.** Short answer for yes/no. Thorough analysis for architectural decisions. Don't pad short answers; don't truncate complex ones.

**Prose by default.** Paragraphs communicate relationships a list cannot. Lists earn their place when items are parallel, independent, and there are 3+ of them.

## Banned Patterns

**Filler.** Never open with: "Sure! I'd be happy to help," "Great question!," "Let me think about that," "Before we dive in." Start with substance.

**Slop words.** Avoid unless precisely right:
- *LLM-isms:* delve, straightforward, comprehensive, notably, fundamentally, profoundly, realm, landscape, tapestry, symphony, testament to
- *Corporate jargon:* leverage, robust, streamline, cornerstone, ever-evolving, cutting-edge, game-changer, paradigm shift
- *Overused intensifiers:* vital, crucial, importantly, genuinely, honestly

**Hedging stacks.** One qualifier per claim. "This might cause issues because..." — not "It might perhaps be worth considering that this could potentially..."

**Not-X-It's-Y pivot.** State what something *is* directly. Don't negate first.
- Bad: "This isn't a bug, it's a design decision."
- Good: "This is a design decision."

**Sausage-making.** Don't narrate implementation steps as summary. Present conclusions directly.

**Narrating the obvious.** Don't inventory what the reader already has — file lists in a diff, commit subjects in the log, UI elements on screen.

**Emphasis inflation.** Bold is for terms being defined or critical warnings. If everything is bold, nothing is.

**Header proliferation.** A section shorter than three sentences rarely needs a header. Three levels maximum.

## What to Preserve

Always keep full detail for: security warnings, irreversible actions, step-by-step procedures where skipping causes errors, error explanations where the *why* matters, nuance that prevents incorrect conclusions.

## Self-Check

Before publishing any documentation:
1. Does the first sentence deliver value?
2. Could any sentence be cut without losing meaning?
3. Are lists earning their keep (3+ parallel items)?
4. Is every technical claim accurate and verifiable?
5. Would the reader feel their time was respected?

## Sources

- Google Technical Writing: https://developers.google.com/tech-writing
- Google Developer Style Guide: https://developers.google.com/style/tone
- best_practices/docs/practices/writing-style.md (internal)
