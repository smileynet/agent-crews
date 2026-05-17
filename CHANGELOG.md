# Changelog

All notable changes to agent-crews are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Protocol skills delivered on-demand to agents — verification, git, and troubleshooting protocols for workers; completion protocol for orchestrators
- Orchestrators get an auto-generated worker table showing who they can delegate to and when — no more hand-maintained lists that drift
- Validation warning when an orchestrator has `read` tool (should delegate reading to workers)
- `@grill-with-docs` prompt — design interrogation that updates CONTEXT.md glossary and ADRs inline as decisions crystallize
- Domain glossary at CONTEXT.md — canonical terms for the project (crew, archetype, dispatcher, etc.)
- Every project gets a dispatcher automatically — routes to your crew leads, plans multi-step work, and handles simple commands directly
- Mark agents as `shared: true` to make them available to all crews in a project (verifier, editor, kiro-helper are shared by default)
- Three-level agent hierarchy for the meta crew — dispatcher routes to leads (build-lead, ops-lead, bugfix-lead), leads coordinate workers
- Bug-fix crew for this repo — systematic debugging of generate.py, scripts, and tooling with independent test verification
- Change-point markers track what changed after each build — use `session-diff --since-change <commit>` to measure impact
- Crew bypass detection, workflow clustering, and agent distribution analysis (`analyze-session.py --bypass-report`, `--clusters`, `--agent-distribution`)
- Session-informed crew recommendations — analyzes your history across oh-my-pi, Codex, kiro-cli, Claude Code, and opencode to pick crews based on what you actually do, not just your tech stack
- `agent-crews build` works from any project directory — no need to be in the agent-crews repo
- Auto-discovery finds all your crew-enabled projects with `just scan`
- Before/after comparison shows whether crew tuning improved token efficiency
- One-shot project analysis and session summary scripts give agents pre-digested data instead of raw parsing
- Rust crew (`rust-lead`, `rust-linter`, `rust-builder`, `rust-tester`) for Rust-specific workflows
- `@handoff` and `@read-handoff` prompts for session continuity across context windows
- Skill manifest at `shared/skills/manifest.yaml` documents which skills auto-load by archetype, which are referenced per crew, and which are user-invoked only — build now refuses unclassified skills

### Fixed
- Component utility agents (verifier, editor) are now automatically available to all orchestrators — previously generated but not wired into dispatch lists
- Projects with components in `.crews/crew.yaml` now get component generation even without a fleet.yaml file
- Orchestrators with explicit `availableAgents` no longer get overwritten by auto-scoping
- Component `allowed_commands` (e.g. `git *`, `cargo check`) now reach worker `toolsSettings.execute_bash.allowedCommands` so kiro-cli can actually enforce them — previously declared but ignored
- Skill references now consistently resolve under `.kiro/skills/` — agents no longer carry broken `skill://shared/skills/...` URIs that fail to load
- Crew-builder's `create-crew` and crew-doctor's `diagnose-crew` skills now ship with deployments — previously referenced but only present in the agent-crews repo itself

### Changed
- **BREAKING:** Meta crew split into three: crew-builder, crew-maintenance, crew-tooling — each follows the standard one-lead-per-file pattern. Leads renamed to crew-builder-lead, crew-maintenance-lead, crew-tooling-lead.
- Orchestrators are pure routers — they delegate all work including file reading, using the injected worker table and delegation rules to decide who gets what
- Dispatcher now delegates reliably — tool permissions enforce routing instead of relying on prompt suggestions alone. Simple file reads still work directly; everything else goes to the right specialist.
- **BREAKING:** No crew defines a dispatcher anymore — it's auto-generated from your project's crew composition
- **BREAKING:** Crew config now lives in your project at `.crews/crew.yaml` instead of centralized in fleet.yaml — commit it, share it, anyone can regenerate from it
- `.kiro/` is now purely kiro-native output (agents, prompts, steering) — no more agent-crews machinery mixed in
- `just build <project>` generates directly in your project (no intermediate staging for normal workflow)
- Evals live with the project at `.crews/evals.yaml` — portable and runnable without the agent-crews repo
- Fleet registry simplified to a name→path mapping in fleet.local.yaml (auto-maintained by scanner)
- Generated `project.md` context is now explicitly runtime-scoped — deployed `.kiro/` artifacts are distinguished from `.crews/` build config, and untouched legacy skeletons auto-upgrade on rebuild
 - `@grill-with-docs` now asks only product-defining design questions, explores codebase-answerable details itself, and presents multiple plausible answers with rationale before recommending one
 - `@handoff` and `@read-handoff` now use a standardized ephemeral handoff artifact with metadata (`created_at`, `base_commit`, `handoff_key`), required briefing sections, and evidence pointers instead of ad hoc summaries

### Added (public-config refactor)
- `workspace:` is a first-class public-config field with `ephemeral:` + `durable:` roots; both required when present, otherwise the product defaults `.scratch` and `.memory` apply
- Every deployed project now ships a `workspace.md` universal steering file describing both roots, their lifecycle, and where the standardized handoff lives
- Shared prompts substitute `{{workspace.ephemeral}}` / `{{workspace.durable}}` so the configured roots flow into `@handoff` / `@read-handoff` without per-prompt edits

### Changed (public-config refactor)
- **BREAKING:** `.crews/crew.yaml` no longer auto-includes `general` — `crews:` is a literal, required, non-empty list; missing or empty `crews:` now fails the build with a clear error
- **BREAKING:** Public-config behavior key renamed from `components:` to `behavior:` (the internal `Component` terminology remains for contributors); update any project configs accordingly

### Removed (public-config refactor)
- **BREAKING:** `theme:` is no longer a public-config field — `shared/themes/`, `_lib/theme.py`, `docs/themed-crews-guide.md`, and the themed-crew test suite are deleted; agent names are always the generic ones from `base/crews/*.yaml`

### Removed
- `vocabulary.md` generation — routing data is now injected directly into agent prompts, eliminating redundant always-loaded context
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
