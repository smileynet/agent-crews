# Examples

Generated crew output for reference. These show what `just build` produces for different project configurations.

## rust-cli (ferris-tracker)

- **Crews:** general + bug-fix (20 agents)
- **Theme:** none
- **Stack:** Rust CLI with cargo build/test/clippy

## node-webapp (taskflow-ui)

- **Crews:** general + infrastructure (19 agents)
- **Theme:** wow (game-themed agent names)
- **Persona:** solutions-architect
- **Stack:** Node/TypeScript with npm build/test/eslint

## godot-game (pixel-dungeon)

- **Crews:** general + content (18 agents)
- **Theme:** none
- **Stack:** Godot with headless build/test

## What's in each example

```
.kiro/
  agents/       Generated agent JSON files
  prompts/      Generated prompt files (including crew-sheet)
  steering/     Component steering files
  scripts/      Utility scripts from components
```

To use these as a starting point, copy the `.kiro/` directory to your project.
