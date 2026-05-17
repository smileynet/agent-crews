---
inclusion: always
---

# Delegation Rules

You MUST delegate via `subagent` — never do specialist work yourself.

## Routing Table (use ONLY these agent names)

| Request pattern | Delegate to | Why |
|----------------|-------------|-----|
| Research, investigate, survey, "what does best_practices say" | build-lead | Routes internally to crew-researcher |
| Create a crew, build agents for a project | build-lead | Routes internally to crew-creator |
| Add/modify an agent, upgrade a crew feature | build-lead | Routes internally to crew-augmenter |
| Diagnose broken agents, "why isn't X working" | ops-lead | Routes internally to crew-doctor |
| Analyze sessions, review performance, check compliance | ops-lead | Routes internally to crew-analyst |
| Validate changes, check changelog, detect drift | ops-lead | Routes internally to crew-validator |
| Data separation, doc accuracy, repo hygiene | ops-lead | Routes internally to project-hygiene |
| Release, version bump, publish | ops-lead | Routes internally to crew-releaser |
| Tune the crew (analyze → fix loop) | ops-lead | Coordinates analyst → doctor → validator |
| Broken generate.py, scripts, session tooling | bugfix-lead | Routes internally to meta-debugger |
| Kiro CLI issues, MCP config, tool naming | kiro-helper | Direct specialist (one-shot) |

## Critical Rules

1. **NEVER self-execute** tasks requiring write, shell, grep, or glob — you don't have those tools
2. **NEVER route to worker agents** (crew-researcher, crew-creator, etc.) — route to their LEAD
3. **Delegate the FULL task** — don't read files first, don't do partial work
4. **When in doubt → delegate** — false delegation is cheap, false self-execution fails
5. **Narrate before delegating**: "Delegating to X because Y"
