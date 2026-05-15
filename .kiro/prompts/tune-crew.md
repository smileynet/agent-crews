---
description: "Full tuning loop: analyze multi-tool sessions, identify crew issues, apply fixes, validate"
---

# Tune Crew

Observe → diagnose → fix → validate loop for a deployed crew.

## Steps

1. **Gather multi-tool session data**
   ```bash
   ./scripts/session-summary.sh <project-path>
   uv run analyze-session.py --compare <project-path>
   ```
   This gives you: tokens/session, failure rate, intent distribution, tool usage across ALL AI tools (oh-my-pi, codex, kiro-cli, claude-code, opencode).

2. **Check crew health**
   ```bash
   ./scripts/crew-health.sh <project-name>
   ```
   Surfaces: dead agents, scope overlaps, missing routing, tool permission issues.

3. **Identify issues** — classify by type:

   | Signal | Issue | Fix |
   |--------|-------|-----|
   | High tokens/session (>500K) | Context waste | Move content from steering to skill, tighten prompts |
   | Failure rate >15% | Tool misconfiguration | Fix allowedCommands, add missing tools |
   | Orchestrator in top tool users | Role bleed | Strengthen "DO NOT implement" boundary |
   | Intent mismatch (session vs crew) | Wrong crews deployed | Add/remove crews per decision matrix |
   | Dead agents in health check | Routing gaps | Fix availableAgents in crew YAML |
   | Same file read 3+ times | Context loss | Add to agent resources |

4. **Apply fixes** — edit crew YAML, steering, or fleet.yaml

5. **Validate**
   ```bash
   just build
   ./scripts/crew-health.sh <project-name>
   ```

6. **Measure improvement**
   ```bash
   ./scripts/session-diff.sh <project-path> <date-of-change>
   ```
   Confirms: tokens down, failures down, delegation up.

## Key Metrics (what to optimize)

| Metric | Target | How to measure |
|--------|--------|----------------|
| Tokens/session | <500K | session-summary.sh |
| Failure rate | <10% | session-summary.sh |
| Delegation ratio | >80% subagent calls from leads | analyze-session.py --stats |
| Intent coverage | All top intents have matching crew | session-summary.sh vs fleet.yaml |

## When NOT to tune

- <5 sessions available (insufficient signal)
- All metrics already healthy (tokens <500K, failures <10%)
- Recent crew change (<3 sessions since last change)
