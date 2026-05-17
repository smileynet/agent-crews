---
name: diataxis-classification
description: "Classify documentation by audience and content type. Use when planning, auditing, or placing project documentation."
---

# Documentation Classification

Two questions: **Who reads this?** then **What do they need?**

## 1. Audience (pick one per document)

| Audience | Entry Point | Voice | Key Question |
|----------|-------------|-------|--------------|
| **Agents** | AGENTS.md | Imperative, terse, verifiable | "What do I DO?" |
| **Users** | README.md | Welcoming, progressive | "How do I USE this?" |
| **Maintainers** | CONTRIBUTING.md | Technical, explains why | "How do I CHANGE this?" |

Mixing audiences in one document serves neither. Split.

## 2. Content Mode (within each audience)

| Mode | Reader State | Structure | Example |
|------|-------------|-----------|---------|
| **Learning** (tutorial) | Beginner | Numbered steps, verify each | "Build your first widget" |
| **Doing** (how-to) | Has a problem | Goal → steps → done | "How to configure auth" |
| **Looking up** (reference) | Needs a fact NOW | Tables, alphabetical | CLI flags, API reference |
| **Understanding** (explanation) | Curious, has time | Prose, diagrams, tradeoffs | "Why event sourcing" |

## 3. Placement

| Type | Path | Litmus Test |
|------|------|-------------|
| Decision (ADR) | `decisions/` | "What did we decide and why?" |
| Specification | `specs/` | "What must the system do?" |
| User guide | top-level or `guides/` | "How does a user do this?" |
| Architecture | `architecture/` | "How is it structured?" |
| Research | `research/` | "What did we learn?" |
| Runbook | `runbooks/` | "What steps fix this?" |

Before placing: check existing folder conventions first. Match what's there.

## 4. Right-Sizing

| Project Maturity | Required Docs |
|-----------------|---------------|
| Weekend hack | README.md |
| Team project (>2 weeks) | + AGENTS.md, CONTRIBUTING.md, architecture doc |
| Multiple contributors | + tutorials, how-tos, ADRs, onboarding guide |
| Public/OSS | + reference, explanation, troubleshooting, glossary |

## Rules

- One audience per document (README is the exception — it routes)
- ADRs are decision records with lifecycle, not "explanation"
- Agent docs are separate from human docs (different requirements)
- Don't create docs nobody will read — right-size to maturity
