# Session Analysis

Agent Crews ingests session logs from 5 AI coding tools to make data-driven crew recommendations.

## Supported tools

| Tool | Location | Data available |
|------|----------|---------------|
| oh-my-pi | `~/.omp/agent/sessions/` | Tokens, model, duration, TTFT |
| Codex | `~/.codex/sessions/` | Tokens, rate limits, git context |
| kiro-cli | `~/.kiro/sessions/cli/` | Messages, tool calls |
| Claude Code | `~/.claude/transcripts/` | Tool calls, results |
| opencode | `~/.local/share/opencode/opencode.db` | Tokens, model, todos |

## How it works

1. `session-ingest.py` reads sessions from all tools and normalizes to a common format
2. Intent classification categorizes user messages (features, bugs, research, etc.)
3. Token usage, failure rates, and tool patterns are aggregated
4. Crew recommendations are generated based on actual work patterns

## Commands

```bash
# Ingest sessions for a project (writes to scratch/sessions/<project>/)
just ingest <project>

# Quick summary (tokens, intents, recommendations)
./scripts/session-summary.sh ~/code/<project>

# Cross-tool comparison
uv run analyze-session.py --compare ~/code/<project>

# Before/after a crew change
./scripts/session-diff.sh ~/code/<project> <date>
```

## What it recommends

| Session signal | Recommendation |
|----------------|---------------|
| >30% bugs/testing intent | Add bug-fix crew |
| >30% research/docs intent | Add research crew |
| >20% infrastructure intent | Add infrastructure crew |
| High tokens/session (>500K) | Enable task_tracking component |
| Failure rate >15% | Enable sanity_gate component |

## Integration with crew creation

When you run `create a crew for ~/code/<project>`, the crew-creator automatically:
1. Scans project files (stack, build tools, structure)
2. Analyzes session history (intents, tokens, failures)
3. Combines both signals to pick crews and configure components

Session data takes priority over static file analysis — what you *do* matters more than what the project *is*.

## Tuning existing crews

Use `@tune-crew` to run the full observe → diagnose → fix → validate loop. It uses session data to identify what's working and what isn't, then measures improvement after changes.
