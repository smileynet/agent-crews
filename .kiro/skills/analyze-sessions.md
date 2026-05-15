---
name: analyze-sessions
description: Analyze sessions across all AI coding tools. Use helper scripts for pre-digested output.
---

# Session Analysis

## Quick commands (use these first)

```bash
# Pre-digested summary (tokens, intents, failures, recommendations)
./scripts/session-summary.sh <project-path>

# Cross-tool comparison table
uv run analyze-session.py --compare <project-path>

# Crew structural health
./scripts/crew-health.sh <project-name>

# Before/after a crew change
./scripts/session-diff.sh <project-path> <date>
```

These scripts handle all parsing. Output is structured and actionable.

## Deep analysis (when scripts aren't enough)

```bash
# Ingest raw sessions into normalized JSONL
uv run session-ingest.py --project <path> --since 30d --output jsonl

# Analyze normalized data
uv run analyze-session.py --normalized scratch/sessions/<project>/all.jsonl

# Kiro-only: single session deep dive
uv run analyze-session.py <session-id> --stats
uv run analyze-session.py <session-id> --compliance
uv run analyze-session.py <session-id> --antipatterns
```

## What to look for

| Metric | Healthy | Action if unhealthy |
|--------|---------|--------------------|
| Tokens/session | <500K | Tighten prompts, add resources, enable task_tracking |
| Failure rate | <10% | Fix allowedCommands, check tool permissions |
| Intent vs crew match | Top intent has matching crew | Add/remove crews |
| Delegation ratio | Leads delegate >80% | Strengthen "DO NOT implement" boundary |

## Tuning loop

Use `@tune-crew` prompt for the full observe → diagnose → fix → validate cycle.
