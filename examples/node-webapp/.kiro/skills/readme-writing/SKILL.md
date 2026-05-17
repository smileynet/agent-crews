---
name: readme-writing
description: "Write and improve README files that orient readers and drive adoption. Use when creating, rewriting, or auditing a project README. Trigger terms: readme, README, project description, quick start, getting started, project documentation entry point."
---

# README Writing

The README is the front door. Most people decide whether to use a project based on the README alone.

## The One-Line Test

The first line (project name + one-sentence description) must answer "what is this?" completely. Test: cover the name, show the rest to someone unfamiliar — can they say what it does?

- Bad: "A tool for document processing built with modern technologies."
- Good: "Convert Markdown files to PDF, HTML, and EPUB from the command line."

Write what the project does, not how it does it.

## Quick Start Is the Most Important Section

Get a reader to a working state in under five minutes. Show real commands, expected output, and minimal required setup. No theory, no background.

```bash
# Good: real commands, expected output, honest about requirements
npm install -g myproject
export MYPROJECT_API_KEY=your_key_here
myproject convert input.md output.pdf
# Converted 3 pages → output.pdf
```

If quick start requires a config file or API key, show that. A quick start that omits a required step manufactures frustration.

## Recommended Section Order

Readers evaluate top-down and stop when they have enough. Put decision-relevant content first:

1. **Project name + one-line description** — what it is
2. **Badges** (optional) — CI, version, license; 3–5 max
3. **What it does** — 2-4 sentences on the problem and approach
4. **Quick start** — fastest path from zero to working
5. **Installation** — full options, platform notes, prerequisites
6. **Usage** — common operations with working examples
7. **Configuration** — options, env vars, config file format
8. **Architecture** (if applicable) — high-level diagram, key components
9. **Development** — how to contribute, build, test, lint
10. **License** — one line or link

Not every project needs every section. Fit structure to the project, but don't invent a new order.

## Show, Don't Tell

Every claim has a runnable example. "Supports many output formats" teaches nothing. A code block demonstrating three formats teaches everything.

## What Doesn't Belong in README

| Content | Where It Goes |
|---------|--------------|
| Agent instructions | AGENTS.md |
| Detailed API reference | Generated docs (Rustdoc, JSDoc, Sphinx) |
| Architecture decisions | docs/adrs/ |
| Research notes | docs/research/ |
| Tutorials | docs/tutorials/ |
| Operational runbooks | docs/ or ops wiki |

## Anti-Patterns

- **Wall of text before quick start** — reader left after paragraph two
- **README as AGENTS.md** — agent tool invocations mixed with human orientation
- **TODO sections** — "TODO: add examples" that hasn't moved in two years. Write it or omit it.
- **Badge bloat** — twelve badges signaling decoration, not quality
- **Quick start that doesn't work** — omits a required step or produces wrong output
- **Screenshots of text** — inaccessible, not copy-pasteable, goes stale
- **Stale version numbers in prose** — "Install v1.2.3" when latest is 2.5.0
- **README that hasn't changed since initial commit** — not wrong, just absent

## Sources

- Art of README (Stephen Whitmore) — README as adoption decision point
- Standard Readme Specification (Richard Litt) — consensus section order
- arXiv 2025 — README and CONTRIBUTING in OSS: early README publication increases contributor activity
- best_practices/docs/practices/readme-writing.md (internal)
