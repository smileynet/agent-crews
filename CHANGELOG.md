# Changelog

All notable changes to agent-crews are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- crew-validator agent for post-change verification (build, changelog, structure, drift, eval coverage)
- crew-releaser agent for release pipeline orchestration (changelog curation, version bump, tag, publish)
- `@release` prompt for guided release workflow
- Changelog component: `standard` variant (verifier checks for entry on user-facing changes)
- Changelog component: `pr-review` variant (draft generation + breaking change detection)
- Changelog-discipline skill with entry quality rules and decision tests
- High reliability design principle (ADR-006) with operational steering
- Auto-chain pattern: crew changes automatically trigger crew-validator
- Deployment setup: crew-creator scaffolds release tooling when changelog component enabled
- Generator validates changelog prerequisites for projects with component enabled

## [0.1.0] - 2026-05-15

### Added
- 8 base crews (general, bug-fix, infrastructure, research, onboarding, hygiene, content, writing) with 58 agents
- Fleet.yaml project registry with component defaults and per-project overrides
- 14 behavioral components (verification, troubleshooting, git, writing, search, memory, notifications, etc.)
- Theme overlay system for cosmetic agent renaming
- Generator: `just build` produces .kiro/agents/*.json from crew YAML + components
- `extends:` mechanism for crew inheritance (remove agents, redefine by name, scope inheritance)
- Per-project vocabulary.md generated from assigned crews
- `file://CONTEXT.md` convention for project domain glossaries
- Orchestrator delegation enforcement (tools-level, not prompt-only)
- Session analysis tooling (`analyze-session.py`)
- Evaluation framework with delegation intent mode and tunable timeouts
- Memory preservation during `just link` redeployment
- Smart crew sync (preserves local `extends:` files while syncing base crews)

### Fixed
- Intent vocabulary normalized across all crews (bugs, research, documentation, implementation)
- Validator only warns on vocab mismatches, not deliberately missing crews
- Tilde expansion in `just link` for fleet.local.yaml paths

[Unreleased]: https://github.com/smileynet/agent-crews/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/smileynet/agent-crews/releases/tag/v0.1.0
