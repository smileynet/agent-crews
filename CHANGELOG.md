# Changelog

All notable changes to agent-crews are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Every project gets a dispatcher automatically — routes to your crew leads, plans multi-step work, and handles simple commands directly
- Mark agents as `shared: true` to make them available to all crews in a project (verifier, editor, kiro-helper are shared by default)
- Three-level agent hierarchy for the meta crew — dispatcher routes to leads (build-lead, ops-lead, bugfix-lead), leads coordinate workers
- Bug-fix crew for this repo — systematic debugging of generate.py, scripts, and tooling with independent test verification
- Dispatcher can execute simple commands directly (≤1 tool call) without routing overhead
- Change-point markers track what changed after each build — use `session-diff --since-change <commit>` to measure impact
- Crew bypass detection, workflow clustering, and agent distribution analysis (`analyze-session.py --bypass-report`, `--clusters`, `--agent-distribution`)
- Session-informed crew recommendations — analyzes your history across oh-my-pi, Codex, kiro-cli, Claude Code, and opencode to pick crews based on what you actually do, not just your tech stack
- `agent-crews build` works from any project directory — no need to be in the agent-crews repo
- Auto-discovery finds all your crew-enabled projects with `just scan`
- Before/after comparison shows whether crew tuning improved token efficiency
- One-shot project analysis and session summary scripts give agents pre-digested data instead of raw parsing

### Fixed
- Component utility agents (verifier, editor) are now automatically available to all orchestrators — previously generated but not wired into dispatch lists
- Projects with components in `.crews/crew.yaml` now get component generation even without a fleet.yaml file
- Orchestrators with explicit `availableAgents` no longer get overwritten by auto-scoping

### Changed
- **BREAKING:** No crew defines a dispatcher anymore — it's auto-generated from your project's crew composition
- **BREAKING:** Crew config now lives in your project at `.crews/crew.yaml` instead of centralized in fleet.yaml — commit it, share it, anyone can regenerate from it
- `.kiro/` is now purely kiro-native output (agents, prompts, steering) — no more agent-crews machinery mixed in
- `just build <project>` generates directly in your project (no intermediate staging for normal workflow)
- Evals live with the project at `.crews/evals.yaml` — portable and runnable without the agent-crews repo
- Fleet registry simplified to a name→path mapping in fleet.local.yaml (auto-maintained by scanner)

### Removed
- `fleet.yaml` — replaced by per-project `.crews/crew.yaml`
- Centralized eval files in `tests/` — each project owns its own evals now

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
