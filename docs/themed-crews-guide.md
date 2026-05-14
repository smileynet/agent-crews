# Themed Crews Guide

Optional game-themed agent names for your projects. Themes are cosmetic overlays — they rename agents without changing behavior.

## Enabling a Theme

In `fleet.yaml`, add `theme: wow` to your project:

```yaml
projects:
  my-project:
    theme: wow
```

Then regenerate: `just build`

Your agents will use themed names instead of generic ones.

## Available Themes

| Theme | Style | Lead Examples |
|-------|-------|--------------|
| `wow` | World of Warcraft / gaming | raid-leader, handler, commander, sage |
| `starcraft` | StarCraft RTS | executor, firebat, overlord, mothership |
| `monster-hunter` | Monster Hunter | guild-master, chief-ecologist, commander, chief-researcher |
| `nautical` | Sailing / naval | captain, damage-control, admiral, expedition-captain |
| `expedition` | Exploration / field science | expedition-leader, medic, logistics-chief, principal-investigator |

### WoW Theme (`theme: wow`)

Game-inspired names from World of Warcraft, Monster Hunter, StarCraft, Final Fantasy, Dark Souls, and D&D.

| Crew | Display Name | Lead | Workers |
|------|-------------|------|---------|
| General | 🎮 Raid Party | `raid-leader` | tactician, scout, warlock, oracle, loremaster, strategist, paladin, shaman, rogue, inspector, champion |
| Bug Fix | 🐛 Bug Hunt | `handler` | quartermaster, tracker, ecologist, trapper, hunter, carver, guild-scribe |
| Infrastructure | 🏗️ Deploy Squad | `commander` | adjutant, arbiter, scv, observer, marine, drone |
| Research | 📚 Lore Guild | `sage` | white-mage, scholar, red-mage, scribe, tonberry, moogle |
| Onboarding | ⚔️ Recon Squad | `ashen-one` | cartographer, lore-hunter, appraiser, blacksmith, crestfallen |
| Hygiene | 🏎️ Pit Crew | `crew-chief` | tire-changer, fuel-man, jack-man, spotter, scrutineer |
| Content | 🎲 Content Crew | `dungeon-master` | bard, wizard, druid, cleric, volo |
| Writing | 📜 Scriptorium | `abbot` | lector, illuminator, scrivener, novice-master, corrector |

## Generic ↔ Themed Name Mapping

| Generic Name | WoW Theme | Crew |
|-------------|-----------|------|
| `general-lead` | `raid-leader` | General |
| `planner` | `tactician` | General |
| `explorer` | `scout` | General |
| `researcher` | `warlock` | General |
| `challenger` | `oracle` | General |
| `advisor` | `loremaster` | General |
| `architect` | `strategist` | General |
| `builder` | `paladin` | General |
| `tester` | `shaman` | General |
| `committer` | `rogue` | General |
| `reviewer` | `inspector` | General |
| `advocate` | `champion` | General |
| `bugfix-lead` | `handler` | Bug Fix |
| `triager` | `quartermaster` | Bug Fix |
| `investigator` | `tracker` | Bug Fix |
| `practices-advisor` | `ecologist` | Bug Fix |
| `reproducer` | `trapper` | Bug Fix |
| `fixer` | `hunter` | Bug Fix |
| `verifier` | `carver` | Bug Fix |
| `documenter` | `guild-scribe` | Bug Fix |
| `infrastructure-lead` | `commander` | Infrastructure |
| `deploy-planner` | `adjutant` | Infrastructure |
| `infra-advisor` | `arbiter` | Infrastructure |
| `provisioner` | `scv` | Infrastructure |
| `monitor` | `observer` | Infrastructure |
| `security-reviewer` | `marine` | Infrastructure |
| `cleanup` | `drone` | Infrastructure |
| `research-lead` | `sage` | Research |
| `outliner` | `white-mage` | Research |
| `internal-researcher` | `scholar` | Research |
| `external-researcher` | `red-mage` | Research |
| `writer` | `scribe` | Research |
| `fact-checker` | `tonberry` | Research |
| `editor` | `moogle` | Research |
| `onboarding-lead` | `ashen-one` | Onboarding |
| `mapper` | `cartographer` | Onboarding |
| `analyst` | `lore-hunter` | Onboarding |
| `auditor` | `appraiser` | Onboarding |
| `restorer` | `blacksmith` | Onboarding |
| `guide-writer` | `crestfallen` | Onboarding |
| `hygiene-lead` | `crew-chief` | Hygiene |
| `doc-checker` | `tire-changer` | Hygiene |
| `deps-checker` | `fuel-man` | Hygiene |
| `structure-checker` | `jack-man` | Hygiene |
| `link-checker` | `spotter` | Hygiene |
| `fix-verifier` | `scrutineer` | Hygiene |
| `content-lead` | `dungeon-master` | Content |
| `narrative-writer` | `bard` | Content |
| `content-researcher` | `wizard` | Content |
| `tutorial-writer` | `druid` | Content |
| `content-reviewer` | `cleric` | Content |
| `publisher` | `volo` | Content |
| `writing-lead` | `abbot` | Writing |
| `doc-auditor` | `lector` | Writing |
| `doc-architect` | `illuminator` | Writing |
| `doc-writer` | `scrivener` | Writing |
| `tutorial-author` | `novice-master` | Writing |
| `doc-verifier` | `corrector` | Writing |

## How Themes Work

- Theme files live in `shared/themes/` (e.g., `shared/themes/wow.yaml`)
- Generator applies the theme at build time: renames JSON files, updates prompts, routing, descriptions
- Theme replaces: agent names, crew display names, welcome messages
- Theme never touches: components, steering rules, tool permissions, behavioral constraints
- Without a theme, agents use their generic descriptive names

## Creating a New Theme

Create `shared/themes/<name>.yaml`:

```yaml
name: my-theme
crews:
  general:
    display: "My Crew Name"
    icon: "🎯"
agents:
  general-lead:
    name: my-custom-lead-name
    welcomeMessage: "Custom welcome message"
  builder:
    name: my-builder-name
    welcomeMessage: "Custom builder welcome"
  # ... map all 58 agents
```

Then set `theme: my-theme` in fleet.yaml and run `just build`.
