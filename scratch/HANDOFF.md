# Handoff — 2026-05-16

## What was being worked on
Build-time context injection (Phases 1+2), meta crew restructure, eval improvements, generate.py modularization, and quality gates.

## Current state
- Phase 1 (protocol skills): ✅ Done
- Phase 2 (orchestrator model): ✅ Done
- Meta crew split (crew-builder/maintenance/tooling): ✅ Done
- Eval harness (parallel 5, fixtures, intent_only, majority-pass): ✅ Done
- 7 eval fixes committed, NOT re-run yet (baseline stale at 28/46)
- generate.py modularization: ✅ Done (9 modules in `_lib/`, 209-line entry point)
- Quality gates: ruff clean, pre-commit config, expanded rules ✅

## Key decisions made
- Orchestrators: no `read`, pure routers, auto-injected worker tables
- Worker tables scoped per crew file (split fixed the bug structurally)
- Eval pass criterion: majority (2/3) not all (3/3)
- `_lib/` at repo root, TypedDict for 3 main shapes, mypy (not ty yet)
- Structural + idempotency tests (no golden files)
- Question bubbling: workers report BLOCKED, leads relay to user

## Next steps (priority order)
1. `just eval` — re-run to confirm fixes improved baseline (expect ~35-40/46)
2. Add `tests/test_validate.py` — hierarchy validation unit tests
3. Add `tests/test_idempotency.py` — run build twice, diff output
4. Add `mypy.ini` with permissive settings, type public function signatures
5. Phase 3 of context injection (`docs/specs/build-time-context-injection.md`):
   - `inject_scope_and_siblings()` — auto-inject scope + sibling list for workers
   - `inject_project_commands()` — from verification config
6. Phase 4 of context injection:
   - `--measure-context` flag on eval harness
   - Token budget tracking in meta.json
   - Test removing `file://AGENTS.md` from workers (keep for orchestrators)
7. Create mock session data fixtures for session-analysis evals
8. Consider splitting `_lib/fleet.py` (460 lines, largest module)
9. Evaluate switching mypy → ty once ty reaches stable

## Context the next session needs
- `_lib/fleet.py` imports from all other _lib modules (it's the orchestrator)
- `_lib/components.py` has a deferred import: `from _lib import deep_merge`
- `get_architypes()` supports both `architypes` and `archetypes` spellings
- `rust.yaml` uses `archetypes` (different from other crew files)
- Shared skills sync to `.kiro/skills/` during build — all references resolve
- `load_fleet_local()` reads fleet.local.yaml (gitignored, per-machine)
- Modularization spec: `docs/specs/generate-modularization.md`
- Context injection spec: `docs/specs/build-time-context-injection.md`
