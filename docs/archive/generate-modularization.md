# Spec: generate.py Modularization and Quality Gates

**Status:** Designed (grill session 2026-05-16)  
**Date:** 2026-05-16  
**Depends on:** Phase 2 complete, eval baseline established

## Grill Session Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| G1 | `_lib/` doesn't need packaging — uv adds script dir to sys.path | No pyproject.toml, no build system, just local imports |
| G2 | TypedDict with `total=False` for 3 main shapes (Crew, AgentJSON, FleetConfig) | Catches misspelled keys without requiring all optional fields |
| G3 | Pre-commit covers ALL Python files (generate.py, _lib/, scripts/) | No reason to allow broken syntax anywhere. Ruff is <100ms. |
| G4 | Big bang extraction in one session (9 commits, tag before starting) | No hybrid state ships. Revert individual commits if broken. |
| G5 | Structural assertions + idempotency test (no golden files) | Golden files break on every prompt tweak. Structural tests catch real invariants. |
| G6 | mypy now, evaluate ty when stable | Standard annotations work with any checker. Swappable later. |
| G7 | Lint the monolith first, then extract | Extraction diffs are pure structural moves, no style noise. |

## Problem

`generate.py` is 1986 lines with 44 functions in a single file. It handles 7 distinct concerns (build, fleet orchestration, injection, sync, theme, components, validation). This makes it:
- Hard to navigate (scrolling 2000 lines to find a function)
- Hard to test (no unit tests, only integration via `just build`)
- Hard to modify safely (changes to theme logic risk breaking build logic)
- Prone to merge conflicts (all changes touch one file)

Additionally, the codebase has no enforced quality gates — ruff is configured but not enforced (13 existing violations), no type checking, no pre-commit hooks, no unit tests.

## Research Findings

### Best Practices
1. **Ruff** (Astral) — all-in-one linter + formatter, runs in milliseconds. Replaces flake8, black, isort. Already partially configured.
2. **ty** (Astral, Rust-based) — new type checker from ruff creators. Faster than mypy, designed for gradual adoption. Still beta but usable for basic checks.
3. **mypy** — mature type checker, works on scripts without pyproject.toml via `mypy script.py`. Stable, well-understood.
4. **pre-commit** — git hooks that run checks before commit. Industry standard for enforcement.
5. **`uv run --script`** — adds script directory to sys.path automatically. Local imports from adjacent directories work without packaging.

### Anti-Patterns
1. **Premature packaging** — converting to pyproject.toml/package when the tool is repo-internal. Adds build system complexity for zero distribution benefit.
2. **Over-splitting** — too many tiny modules requiring 8 file jumps to understand one flow. Modules should be 50-200 lines, not 10-20.
3. **Type annotations everywhere at once** — gradual typing is better. Start with public function signatures, skip internals.
4. **Circular imports** — splitting without mapping dependency direction first. Must extract leaf modules (no deps) before core modules.
5. **Enforcing too strictly too fast** — going from 0 to strict mypy in one commit creates hundreds of errors. Gradual adoption with `--ignore-missing-imports` and per-file overrides.

### Prior Art (uv scripts)
- `uv run --script` adds script dir to `sys.path` — local imports work
- Inline deps (`# /// script`) only apply to entry point, submodules inherit
- No packaging needed for repo-internal tools

## Design

### Module Structure

```
generate.py                    Entry point: argparse + dispatch (~100 lines)
_lib/                          Internal modules (underscore = private)
  __init__.py                  Empty
  types.py                     TypedDict definitions for crew, agent, config (~30 lines)
  build.py                     build_agent, generate, resolve_extends, deep_merge (~250 lines)
  fleet.py                     generate_all, load_fleet_config/local, resolve_project (~300 lines)
  inject.py                    synthesize_dispatcher, inject_subagents, worker_table (~200 lines)
  sync.py                      sync_steering, sync_skills, sync_prompts (~80 lines)
  theme.py                     load_theme, apply_theme_to_agents (~100 lines)
  components.py                component loading, steering, subagents (~150 lines)
  validate.py                  validate_hierarchy, validate_coverage, check_health (~120 lines)
  utils.py                     crew_sheet, routing_table, sibling_map, project_md (~100 lines)
```

### Why `_lib/` not `lib/` or a package
- Underscore signals "internal, don't import externally"
- At repo root = Python finds it automatically (same dir as generate.py)
- No `pyproject.toml` needed
- `uv run generate.py` continues to work unchanged
- Gitignore-friendly (won't be confused with a deployable package)

### Quality Gates

#### Layer 1: Syntax and Style (immediate — enforce now)

| Tool | Config | Enforcement |
|------|--------|-------------|
| ruff check | `ruff.toml` (already exists) | pre-commit hook + mise task |
| ruff format | `ruff.toml` | pre-commit hook + mise task |

Rules to enable beyond defaults:
```toml
[lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
# E=pycodestyle, F=pyflakes, W=warnings, I=isort
# UP=pyupgrade, B=bugbear, SIM=simplify
```

#### Layer 2: Type Safety (gradual — after modularization)

| Tool | Config | Enforcement |
|------|--------|-------------|
| mypy | `mypy.ini` or `[tool.mypy]` in ruff.toml | CI check (warning initially, error after coverage reaches 80%) |

Gradual adoption strategy:
1. Add `types.py` with TypedDict for crew config, agent JSON, fleet config
2. Type public function signatures in each module as extracted
3. Run mypy with `--ignore-missing-imports --allow-untyped-defs`
4. Tighten per-module as coverage improves

#### Layer 3: Testing (after modularization)

| Tool | Config | Enforcement |
|------|--------|-------------|
| pytest | `tests/` directory | mise task + pre-commit (fast tests only) |

Test strategy:
- Structural assertions: invariants that must hold regardless of prompt content
- Idempotency test: `just build` twice → identical output (catches non-determinism)
- No golden files (break on every prompt tweak, high maintenance for low value)

#### Layer 4: Pre-commit Hooks (enforcement mechanism)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: generate-dry-run
        name: generate.py syntax check
        entry: python3 -c "import ast; ast.parse(open('generate.py').read())"
        language: system
        files: generate.py|_lib/.*\.py
        pass_filenames: false
```

#### Layer 5: CI (GitHub Actions)

```yaml
# .github/workflows/quality.yml
name: Quality
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install mypy pyyaml
      - run: mypy generate.py _lib/ --ignore-missing-imports
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv run generate.py --dry-run
```

### Dependency Graph (extraction order)

```
validate.py  ←── no deps (pure functions, extract first)
theme.py     ←── no deps (yaml, json, re only)
sync.py      ←── no deps (shutil, Path only)
utils.py     ←── depends on: yaml (crew_sheet needs to read YAML)
components.py ←── depends on: sync (writes steering)
types.py     ←── no deps (just TypedDict definitions)
build.py     ←── depends on: types, validate (core build logic)
inject.py    ←── depends on: types, build (needs crew structure)
fleet.py     ←── depends on: build, inject, sync, theme, components, utils (orchestrator)
```

## Implementation Plan

### Phase A: Quality Gates (do first, before splitting)

1. Fix existing 13 ruff violations (`ruff check --fix`)
2. Expand ruff config (add I, UP, B, SIM rules)
3. Add pre-commit config with ruff + AST syntax check
4. Add `just lint` and `just format` to justfile
5. Update mise tasks

**Commit:** `chore: enforce ruff linting and formatting`

### Phase B: Type Foundation

1. Create `_lib/types.py` with TypedDict definitions
2. Add `mypy.ini` with permissive settings
3. Type the 5 most-used function signatures
4. Add mypy to mise tasks (warning, not blocking)

**Commit:** `chore: add type definitions and mypy config`

### Phase C: Module Extraction (one per commit)

1. Extract `_lib/validate.py` — verify `just build` still works
2. Extract `_lib/theme.py` — verify
3. Extract `_lib/sync.py` — verify
4. Extract `_lib/utils.py` — verify
5. Extract `_lib/components.py` — verify
6. Extract `_lib/build.py` — verify
7. Extract `_lib/inject.py` — verify
8. Extract `_lib/fleet.py` — verify
9. Slim `generate.py` to entry point — verify

**Each commit:** extract module, update imports, run `just build --all`, confirm no behavior change.

### Phase D: Testing

1. Add `tests/test_validate.py` — hierarchy validation unit tests
2. Add `tests/test_build.py` — structural assertions (workers no subagent, orchestrators have worker table, dispatcher has all leads)
3. Add `tests/test_idempotency.py` — run build twice, diff output
4. Add to CI

**Commit:** `test: add unit tests for core modules`

## Risks

| Risk | Mitigation |
|------|------------|
| Breaking `uv run generate.py` | Test after every extraction. Entry point stays unchanged. |
| Circular imports | Extract leaf modules first (validate, theme, sync). Map deps before extracting core. |
| Import path issues | `_lib/` at repo root = automatic sys.path inclusion. Verified with uv docs. |
| Over-engineering | Stop at 8-9 modules. Don't split further unless a module exceeds 300 lines. |
| Type annotation burden | Gradual — start with public signatures only. `--allow-untyped-defs` initially. |
| Pre-commit slowing workflow | Ruff runs in <100ms. AST parse in <50ms. Total hook time <200ms. |

## Success Criteria

1. `generate.py` is <150 lines (entry point only)
2. No module exceeds 300 lines
3. `ruff check` passes with zero violations
4. `just build --all` produces identical output before and after
5. Pre-commit hooks catch syntax errors and style violations before commit
6. At least 5 unit tests covering validation and build logic
7. mypy runs without errors on typed modules

## Timeline

- Phase A: 30 minutes (fix lint, add hooks)
- Phase B: 30 minutes (types, mypy config)
- Phase C: 2 hours (9 extraction commits)
- Phase D: 1 hour (unit tests)
- Total: ~4 hours

## Decision: When to Start

After the eval baseline is established (task 5 of current work). The refactoring is pure structural — no behavior change — but it's easier to verify against a known-good baseline. If evals pass before and after, the refactoring is correct.
