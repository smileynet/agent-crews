# Handoff — 2026-05-17

## What was being worked on
Closing out the deployment-pipeline gaps: regenerated stale examples, addressed Gap 2 (skill manifest), curated the [Unreleased] CHANGELOG for the post-0.2.0 trajectory.

## Current state
- Tests: ✅ 67 passing (`just test`), 0 skipped
- mypy: ✅ Clean on `_lib/` + `generate.py`
- ruff: ✅ Clean on `_lib/` + `generate.py` (4 pre-existing F401 in tests/ untouched)
- Examples + self-host: fully regenerated and committed
- Eval baseline: ❌ Still stale at 28/46 (commit 507b055 baseline, ~12h before HEAD)

## What landed this session
- `chore: regenerate examples and self-host outputs` (b8b9153) — picked up the skill-path fix from e9cdb16 plus the `allowedCommands` feature from c31b48c
- Gap 2 (skill manifest): `shared/skills/manifest.yaml` classifies every skill as archetype-auto-injected / crew-referenced / user-only. `_lib/skills.py` loads it; `_lib/build.py` drives worker/orchestrator skill injection from the manifest instead of hardcoded lists. `test_manifest_classifies_all_skills` enforces every disk skill is classified.
- Skill-path drift: 3 meta-crew agents had `skill://shared/skills/...` references that don't resolve at runtime. Fixed in `base/crews/crew-{builder,maintenance,tooling}.yaml`.
- Orphan skills: `create-crew.md` and `diagnose-crew.md` lived only in `.kiro/skills/` (not `shared/skills/`), so they never deployed to other projects. Moved to source.
- CHANGELOG: added Rust crew, `@handoff`/`@read-handoff`, skill manifest under Added; added allowed_commands, skill-path consistency, and create-crew/diagnose-crew shipping under Fixed.
- Deployment-gaps proposal: marked Gap 1 and Gap 2 done; Gap 3 deferred (external kiro-cli feature).

## Next steps
1. `just eval` — re-run the 46-case suite. Baseline expects ~35-40 after the accumulated fixes; update CHANGELOG numbers if relevant.
2. Fix `results/latest` symlink — currently points at a 1-case smoke run, not the full 46-case suite.
3. Cut a release. [Unreleased] now has 3 BREAKING changes (.crews/ separation, no-crew-defines-dispatcher, meta-crew split) plus significant additive work. Plausibly 0.3.0 or 1.0.0.
4. Wire CI: GitHub Actions running `just test` + ruff + mypy. Pre-commit catches local; CI catches PRs.
5. Gap 3: file the kiro-cli `inclusion: agent_match` feature request when context arises.
6. Pre-existing nit: clean up 4 F401 unused imports in `tests/{test_build,test_e2e,test_pipeline,test_validate}.py` — `uv run --with ruff ruff check tests/ --fix`.

## Context the next session needs
- The skill manifest is the new single source of truth for archetype-scoped skills. To add a new protocol skill, drop it in `shared/skills/`, list it under `archetype.worker` or `archetype.orchestrator` in `shared/skills/manifest.yaml`, then `just build`.
- `_lib/skills.py::skill_reference` picks the SKILL.md vs single-file shape automatically based on what's on disk.
- Component subagents (verifier, editor from components) deliberately skip archetype injection — they run in fresh context. The manifest test exempts them via the `hooks` absence heuristic.
