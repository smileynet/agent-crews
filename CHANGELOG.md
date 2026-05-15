# Changelog

All notable changes to agent-crews are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-15

### Added
- Changes are automatically validated after every crew modification (build, changelog, structure, drift)
- Release workflow with guided changelog curation, version bumping, and platform publishing
- Projects can opt into changelog discipline that catches missing entries before completion
- Behavioral changes now prompt for eval re-runs to catch regressions early
- 3-level agent hierarchy: a dispatcher routes to crew leads, crew leads delegate to workers
- Build-time enforcement catches hierarchy violations before deployment
- Relay protocol ensures research findings reach downstream agents automatically
- Crew leads report aggregated outcomes to dispatchers with structured signals
- Workers check for prior research before starting tasks
- Experiment template for testing new agent behaviors in isolation

### Changed
- Dispatcher is now a distinct archetype type with its own routing rules

## [0.1.0] - 2026-05-15

### Added
- Deploy specialized AI agent teams to any project with one command (`just build`)
- 8 crew types for different work: general, bug-fix, infrastructure, research, onboarding, hygiene, content, writing
- Mix and match crews per project — configure in fleet.yaml, generate once, deploy everywhere
- Inherit and customize base crews without forking (`extends:` with agent removal and replacement)
- 14 behavioral components shape how agents work (verification gates, git workflow, troubleshooting escalation, etc.)
- Theme overlay gives agents character without changing behavior (e.g., WoW-themed names)
- Orchestrators delegate, they don't absorb — enforced at the tools level, not just prompts
- Per-project vocabulary keeps agents aligned on domain language
- Domain glossary (`CONTEXT.md`) automatically available to all deployed agents
- Analyze past sessions to find crew performance issues and recommend improvements
- Test crew behavior with model-based evals (delegation intent mode for fast feedback)
- Redeployment preserves project memory (lessons learned survive `just link`)

### Fixed
- Crews use consistent intent vocabulary (no more mismatches between "bug-fixing" and "bugs")
- Redeployment to paths with `~` now works correctly

[Unreleased]: https://github.com/smileynet/agent-crews/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/smileynet/agent-crews/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/smileynet/agent-crews/releases/tag/v0.1.0
