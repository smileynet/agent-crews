# Spec: Generic Base Crews + Theme Overlay

**Status:** Implemented  
**Date:** 2026-05-11

## Problem

Themes are baked into crew YAMLs (agent names like "raid-leader", "paladin" ARE the theme). This couples cosmetic identity to capability, prevents reuse, and per research, persona-style naming may hurt performance on coding tasks.

## Design Decisions

### D1: Theming is cosmetic, applied at project level
- Base crews use generic descriptive names
- Theme is an optional overlay that renames agents + adds voice
- Default: no theme (generic names)
- Constraints (components) are never themed

### D2: General crew is the only default deployment
- New projects get ONE crew: general (12 agents)
- Specialized crews are opt-in additions
- Routing rules in general-lead suggest switching when appropriate
- Progressive complexity: start simple, add when you feel pain

### D3: 8 distinct crew rosters (genuinely different agent compositions)
- general (12) — handles everything
- bug-fix (8) — debugging workflow
- infrastructure (7) — deploy/destroy
- research (6) — investigation/docs
- onboarding (5) — brownfield repos
- hygiene (6) — project maintenance
- content (6) — presentations/tutorials
- writing (6) — prose/editing

### D4: Agent naming convention
- Orchestrators: `{crew}-lead` (always, including `general-lead`)
- Workers: unique descriptive name, no crew prefix
- Worker names globally unique across all deployed crews
- All descriptions prefixed with `[Crew Name]` for visual grouping

### D5: Routing auto-generated from agent declarations
- Each agent declares a `routes:` field ("send me work when: ...")
- Generator assembles routing table into orchestrator prompt
- Adding/removing agents automatically updates routing
- Theme overlay renames agents in the routing table

### D6: Theme overlay mechanics
- Shared themes in `shared/themes/` (reusable presets: wow, monster-hunter, starcraft, etc.)
- Projects reference by name in fleet.yaml: `theme: wow`
- Theme file maps: generic name → themed name + crew display name
- Generator applies at generation time: renames JSON files, updates prompts/routing/descriptions
- Theme replaces: agent names, crew display names, welcome messages, narration voice
- Theme never touches: components, steering rules, tool permissions, behavioral constraints

### D7: Crew-sheet auto-generated
- Generator produces `.kiro/prompts/crew-sheet.md` from deployed agents
- Lists all crews, agents (grouped by crew), descriptions, keyboard shortcuts
- Reflects themed names when theme is active
- Updates automatically on `just build`

### D8: Theme file format
```yaml
# shared/themes/wow.yaml
name: wow
crews:
  general: { display: "Raid Party", icon: "🎮" }
  bug-fix: { display: "Bug Hunt", icon: "🐛" }
  infrastructure: { display: "Deploy Squad", icon: "🏗️" }
  research: { display: "Lore Guild", icon: "📚" }
  onboarding: { display: "Recon Squad", icon: "⚔️" }
  hygiene: { display: "Pit Crew", icon: "🏎️" }
  content: { display: "Content Crew", icon: "🎲" }
  writing: { display: "Scriptorium", icon: "📜" }
agents:
  general-lead: { name: raid-leader }
  planner: { name: tactician }
  explorer: { name: scout }
  researcher: { name: warlock }
  architect: { name: strategist }
  builder: { name: paladin }
  tester: { name: shaman }
  reviewer: { name: inspector }
  committer: { name: rogue }
  challenger: { name: oracle }
  advocate: { name: champion }
  advisor: { name: loremaster }
  bugfix-lead: { name: handler }
  # ... etc
voice:
  tone: "Confident raid leader calling targets"
  vocabulary_use: [pull, wipe, aggro, DPS, tank, healer, buff]
  vocabulary_avoid: [deploy, ship, release, sprint]
```

### D9: Fleet.yaml configuration
```yaml
defaults:
  crews: [general]
  theme: null  # no theme by default

projects:
  my-game-project:
    crews: [general, bug-fix, content]
    theme: wow
  my-rust-project:
    crews: [general]
    theme: null  # generic names
```

## General Crew Agent Roster

| Name | Role | Routes (send work when...) |
|------|------|---------------------------|
| `general-lead` | Orchestrator | Entry point for all work |
| `planner` | Planner | Complex work needs sequencing |
| `explorer` | Code explorer | Need to find/understand local code |
| `researcher` | Deep researcher | Need external info, deep investigation |
| `architect` | Architect | Need design decisions, structure |
| `builder` | Builder | Need code written, builds run |
| `tester` | Tester | Need tests written/run |
| `reviewer` | Reviewer | Need code reviewed (read-only) |
| `committer` | Git ops | Need commits, branches, PRs |
| `challenger` | Challenger | Need blind spot check, zoom out |
| `advocate` | Advocate | Need problem validation, JTBD check |
| `advisor` | Advisor | Need best practices, prior art |

## Research Backing

- **Google DeepMind/MIT (2025):** Multi-agent coordination degrades sequential task performance 39-70%. Single well-configured agent outperforms for most coding work.
- **Progressive Complexity Escalation (Agentic Patterns):** Start simple, unlock complexity as trust is established.
- **Persona vs Constraints (Jared Foy/RESOLVE, 2026):** Persona declarations are theater; constraints do the real work. For coding tasks, persona prompting produces worse results.
- **Anthropic (2026):** Multi-agent outperforms single by 90.2% but consumes 15x more tokens. Token usage explains 80% of performance differences.
- **SWE-bench (2026):** Multi-agent coding team achieves 72.2% vs 65% solo — 7-point improvement justified by objective test signals (adversarial verification).

## Implementation Order

1. Write generic `base/crews/general.yaml` (extract from current raid-party, remove theme)
2. Write remaining 7 generic crew YAMLs
3. Create `shared/themes/wow.yaml` (extract current themed names)
4. Update generator: theme overlay, crew-sheet generation, routes auto-assembly
5. Update fleet.yaml: `crews:` and `theme:` fields
6. Regenerate all projects
7. Create remaining theme files (monster-hunter, starcraft, etc.)

## Migration

- Current themed crews → extract generic base + theme file
- No behavioral change for existing projects (same constraints, just renamed)
- Projects with `theme: wow` get identical output to current state
- Projects with `theme: null` get generic names (new capability)
