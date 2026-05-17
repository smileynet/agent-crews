# base — Base Crew Template

Source of truth for all generic crew definitions. Contains 8 crews with 58 agents total.

## Structure

```
base/
├── crews/                     # 8 generic crew definitions
│   ├── general.yaml           # General purpose (12 agents)
│   ├── bug-fix.yaml           # Bug fixing (8 agents)
│   ├── infrastructure.yaml    # Infrastructure/deploy (7 agents)
│   ├── research.yaml          # Research/docs (7 agents)
│   ├── onboarding.yaml        # Brownfield onboarding (6 agents)
│   ├── hygiene.yaml           # Project maintenance (6 agents)
│   ├── content.yaml           # Presentations/tutorials (6 agents)
│   └── writing.yaml           # Writing/editing (6 agents)
└── agents/                    # Generated .json files (gitignored, do not edit)
```

## How It Works

1. Crew YAMLs define: agent roster + delegation rules + scope + routes
2. Behavioral rules come from `shared/components/` (not inline in crew prompts)
4. `generate.py --all` produces `.json` agent files + steering + crew-sheet for each project
5. Projects in `projects/` get crews synced from here (unless they have `.custom-crews`)
6. `.crews/crew.yaml` controls which crews each project gets (`crews:` field)

## Crew YAML Format

```yaml
workflow: <crew-name>

scope:
  handles: [features, mixed-work]
  refuses: [bug-fixing, infrastructure]

architypes:
  - type: orchestrator
    agents:
      - name: <crew>-lead
        description: "[Crew] Orchestrator — ..."
        routes: "Entry point for ..."

  - type: worker
    agents:
      - name: <worker>
        description: "[Crew] Role — ..."
        routes: "Send work when ..."
```

## Adding a New Crew

1. Create `base/crews/<name>.yaml` following the format above
2. Add `scope:` declaration (handles/refuses)
3. Add `routes:` to each agent
4. Run `just build`
6. Update AGENTS.md crew table

## Design Principles

- Generic descriptive names by default
- Crew prompts contain ONLY identity + delegation + routing + scope
- Behavioral rules (verification, git, troubleshooting, etc.) live in components
- Each crew declares what it handles and refuses (for handoff routing)
- Workers are autonomous — tell them WHAT, not HOW
- Routing auto-generated from `routes:` fields into orchestrator prompts
