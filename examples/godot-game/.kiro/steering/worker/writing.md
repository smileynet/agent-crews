---
inclusion: always
---
# Writing Protocol

## Style
Follow the writing-style skill. Key principles:
- Direct and concise — cut hedging, filler, and obvious statements
- One idea per paragraph
- Active voice preferred
- Technical precision over vague generality

## Placement
Before creating a new document, determine its location:
1. Check existing project conventions (folder structure, docs README)
2. Apply docs-organization skill for type → path mapping
Never create documents without verifying placement first.

## Editor Triggers
The editor agent fires on:
- **New document** — any new .md, README, or user-facing doc
- **Significant revision** — changes >5 lines to existing docs
- **User-facing artifacts** — PR descriptions, commit messages for shared repos, ADRs

The editor sees: document + style rules only (NOT your reasoning).
The editor returns: specific edits or "clean" (no changes needed).

## Theme
If a theme is configured (theme.yaml), apply themed voice to:
- Narration and status updates
- Welcome messages and handoff redirects
- Notifications

Theme does NOT apply to:
- Committed artifacts (docs, PRs, commits, ADRs)
- Code comments
- Technical specifications
