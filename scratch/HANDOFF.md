# Handoff — 2026-05-16

## What was being worked on
Build-time context injection (Phases 1+2), meta crew restructure, eval harness improvements, and quality gate setup for generate.py modularization.

## Current state
- **Phase 1 (protocol skills):** ✅ Done — workers get verification/git/troubleshooting, orchestrators get completion
- **Phase 2 (leads):** ✅ Done — read removed from orchestrators, worker table injected, vocabulary.md removed
- **Meta crew restructure:** ✅ Done — split into crew-builder, crew-maintenance, crew-tooling (3 files, one lead each)
- **Dispatcher prompt:** ✅ Fixed — routes on intent not completeness, question bubbling relay added
- **Eval harness:** ✅ Updated — copy-based isolation, fixtures, intent_only, parallel 5, majority-pass criterion
- **Evals:** ✅ 46 total, baseline 28/46 (61%), expected ~35-40 after latest fixes (not re-run yet)
- **Quality gates:** ✅ Phase A done — ruff clean, pre-commit config added, expanded rules
- **Modularization:** Spec written and grilled. Phase C (extraction) NOT started — deferred to next session.

## Key decisions made
- Orchestrators are pure routers (no read tool, delegate everything)
- Worker tables auto-injected from same-crew-file workers (fixes scoping bug)
- vocabulary.md removed (redundant with routing table injection)
- Meta crew split into 3 files following base crew pattern
- Eval pass criterion: majority-pass (2/3) not all-pass (3/3)
- generate.py modularization: `_lib/` at repo root, TypedDict, structural+idempotency tests, mypy, lint-first-then-extract, big-bang in one session

## Files modified
- `generate.py` — injection logic, dispatcher prompt, skill sync, vocabulary removal
- `base/crews/crew-builder.yaml`, `crew-maintenance.yaml`, `crew-tooling.yaml` — new
- `base/crews/meta.yaml` — deleted
- `scripts/eval-crew.py` — parallel, fixtures, intent_only, majority-pass
- `.crews/evals.yaml` — 46 evals, fixtures, intent_only, rewritten cases
- `AGENTS.md`, `CONTEXT.md`, `CHANGELOG.md` — updated for restructure
- `docs/specs/build-time-context-injection.md` — Phases 1+2 marked done
- `docs/specs/generate-modularization.md` — full spec with grill decisions
- `shared/skills/` — 4 new protocol skills
- `shared/prompts/` — grill-with-docs, handoff, read-handoff
- `.pre-commit-config.yaml`, `ruff.toml`, `.mise.toml` — quality gates

## Next steps
1. **Re-run evals** to confirm latest fixes improved baseline: `just eval`
2. **generate.py modularization** — follow spec at `docs/specs/generate-modularization.md`:
   - Tag current commit as safety net
   - Create `_lib/` with `__init__.py`
   - Extract in order: validate → theme → sync → utils → components → build → inject → fleet
   - Run `just build --all` after each extraction
   - Slim generate.py to entry point
3. **Phase B** (types) — add `_lib/types.py` with TypedDict, add mypy
4. **Phase D** (tests) — structural assertions + idempotency test

## Context the next session needs
- The eval run with fixes hasn't been re-run yet (the 28/46 baseline was BEFORE the 7 fixes)
- `base/crews/rust.yaml` uses `archetypes` spelling (not `architypes`) — both are supported by `get_architypes()`
- Shared skills are now synced to `.kiro/skills/` during build — all 21 previously-missing references resolved
- The `_lib/` directory doesn't exist yet — create it fresh when starting extraction
