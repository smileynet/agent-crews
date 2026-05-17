# Handoff — 2026-05-16

## What was being worked on
Build-time context injection (Phases 1+2), meta crew restructure into 3 files, eval harness improvements, and prep for generate.py modularization.

## Current state
- Phases 1+2: ✅ Done and committed
- Meta crew split (crew-builder/maintenance/tooling): ✅ Done
- Eval harness (parallel, fixtures, intent_only, majority-pass): ✅ Done
- 7 eval fixes committed but NOT re-run yet — baseline is stale (28/46 pre-fix)
- Ruff lint clean + pre-commit config: ✅ Done
- generate.py modularization: spec written (`docs/specs/generate-modularization.md`), NOT started

## Key decisions made
- Orchestrators have no `read` — pure routers with auto-injected worker tables
- Pass criterion: majority (2/3) not all (3/3)
- Modularization: `_lib/` at repo root, TypedDict, structural+idempotency tests, mypy, big-bang extraction in one session
- Lint monolith first, then extract (done — lint is clean)

## Files modified
- `generate.py` — injection, dispatcher prompt, skill sync, lint fixes
- `base/crews/crew-builder.yaml`, `crew-maintenance.yaml`, `crew-tooling.yaml` — new (meta.yaml deleted)
- `scripts/eval-crew.py` — parallel, fixtures, intent_only, majority-pass, lint
- `.crews/evals.yaml` — 46 evals with fixtures, intent_only, rewritten cases
- `AGENTS.md`, `CONTEXT.md`, `CHANGELOG.md`, `docs/specs/build-time-context-injection.md`
- `docs/specs/generate-modularization.md` — full spec with grill decisions
- `ruff.toml`, `.pre-commit-config.yaml`, `.mise.toml` — quality gates
- `shared/prompts/handoff.md`, `read-handoff.md`, `grill-with-docs.md`
- `shared/skills/{verification,git,troubleshooting,completion}-protocol/SKILL.md`

## Next steps
1. `just eval` — re-run evals to confirm 7 fixes improved baseline (expect ~35-40/46)
2. Start generate.py modularization per `docs/specs/generate-modularization.md`:
   - `git tag -m "pre-modularization" pre-modularization`
   - `mkdir -p _lib && touch _lib/__init__.py`
   - Extract in order: validate → theme → sync → utils → components → build → inject → fleet
   - `just build --all` after each extraction commit
3. Add `_lib/types.py` with TypedDict (CrewConfig, AgentJSON, FleetConfig)
4. Add `tests/` with structural assertions + idempotency test

## Context the next session needs
- `get_architypes()` is used everywhere — it supports both `architypes` and `archetypes` spellings
- `rust.yaml` uses `archetypes` (different from all other crew files using `architypes`)
- Shared skills sync to `.kiro/skills/` during build — all references now resolve
- The `synthesize_dispatcher()` function at line ~1500 builds shared_lines with routing hints from crew files
- `validate_hierarchy()` at line ~650 depends on `get_architypes()` — extract together or import it
