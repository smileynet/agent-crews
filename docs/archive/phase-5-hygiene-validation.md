# Spec: Phase 5 — Hygiene Validation

**Status:** Planned  
**Date:** 2026-05-13  
**Depends on:** Phases 2, 3, 1, 4 (validates all prior work)

## Objective

Run the project-hygiene agent against the repo to validate all phases completed correctly. This is both a one-time validation gate and an ongoing drift-detection mechanism.

## Validation Checks

The project-hygiene agent performs these checks:

### Data Separation (Phase 1)

| # | Check | Pass Criteria |
|---|-------|---------------|
| 1 | fleet.yaml is gitignored | `git check-ignore fleet.yaml` returns 0 |
| 2 | projects/ is gitignored | `git check-ignore projects/foo` returns 0 |
| 3 | No personal project names in committed files | grep for known names returns empty |
| 4 | fleet.example.yaml exists | File present, valid YAML |
| 5 | fleet.example.yaml contains no real project data | No personal Slack IDs, no real paths |
| 6 | fleet.example.yaml uses `persona: personal` as default | Not `sa` or other personal personas |

Known personal project names to scan for:
- (maintained in scripts/validate.sh — the canonical blocklist)

### Meta Crew (Phase 2)

| # | Check | Pass Criteria |
|---|-------|---------------|
| 7 | base/crews/meta.yaml exists | File present, valid YAML |
| 8 | Meta crew defines all expected agents | dispatcher, crew-creator, crew-augmenter, crew-doctor, crew-analyst, crew-researcher, kiro-helper, project-hygiene |
| 9 | Meta crew defines all expected prompts | grill-me, create-crew, deploy-crew, crew-sheet, review-crew-quality, review-session, review-crew, tune-crew |

### Generation (Phase 3)

| # | Check | Pass Criteria |
|---|-------|---------------|
| 10 | .kiro/agents/ matches meta crew roster | One JSON per agent defined in meta.yaml |
| 11 | .kiro/prompts/ matches meta crew prompts | One MD per prompt defined in meta.yaml |
| 12 | Generation is idempotent | `just build agent-crews && just build agent-crews && git diff --exit-code .kiro/` |

### Documentation (Phase 4)

| # | Check | Pass Criteria |
|---|-------|---------------|
| 13 | README references fleet.example.yaml | String present |
| 14 | README does NOT reference fleet.yaml as a committed file | No "edit fleet.yaml" instructions |
| 15 | AGENTS.md matches .kiro/agents/*.json | Every agent listed, descriptions match |
| 16 | AGENTS.md contains no `sa-crew/crews/` references | Stale paths removed |
| 17 | AGENTS.md contains no personal project names | Scrubbed |
| 18 | CONTRIBUTING.md exists | File present with crew/component/theme sections |
| 19 | No broken internal links | All relative paths in .md files resolve |

### Examples (Final Step)

| # | Check | Pass Criteria |
|---|-------|---------------|
| 20 | examples/ directory exists | At least 2 subdirectories |
| 21 | Each example has .kiro/agents/ | At least 1 agent JSON per example |
| 22 | Each example has .kiro/prompts/ | At least 1 prompt MD per example |
| 23 | Example agents are valid JSON | Parse without error |

**Note:** Examples checks (20-23) only apply after the final generation step. They are not blocking during Phase 5 execution — they validate the final output.

## Execution

```bash
# Invoke the project-hygiene agent
# (via dispatcher or directly)
@project-hygiene Run full validation pass
```

Or as a script for CI:

```bash
#!/bin/bash
set -e

# Check 1-2: gitignore
git check-ignore fleet.yaml
git check-ignore projects/placeholder

# Check 3: no personal names
NAMES="<see-validate-sh-for-blocklist>"
if git grep -lE "$NAMES" -- ':!docs/specs/phase-5-hygiene-validation.md'; then
  echo "FAIL: Personal project names found in committed files"
  exit 1
fi

# Check 4: fleet.example.yaml valid
python -c "import yaml; yaml.safe_load(open('fleet.example.yaml'))"

# Check 12: generation idempotent
just build agent-crews
just build agent-crews
git diff --exit-code .kiro/

echo "ALL CHECKS PASSED (pre-examples)"
```

## Final Step: Generate Examples

After all checks (1-19) pass, generate `examples/` from the working system:

```bash
just build ferris-tracker taskflow-ui pixel-dungeon
# Copy generated output to examples/
cp -r projects/ferris-tracker examples/rust-cli
cp -r projects/taskflow-ui examples/node-webapp
cp -r projects/pixel-dungeon examples/godot-game
```

Then validate checks 20-23.

This is the LAST action before the squash-merge commit. Examples are real generated artifacts from the working system, not hand-written.

## Ongoing Use

This is not a one-shot phase. After initial validation:

- Run project-hygiene weekly or before releases
- Add to CI as a lint step
- Catches drift: someone adds a personal project name to a doc, AGENTS.md gets stale, examples become outdated

## Severity Classification

| Severity | Examples | Action |
|----------|----------|--------|
| BLOCKING | Personal data in committed files, broken generation, idempotency failure | Fix immediately |
| DRIFT | AGENTS.md doesn't match .kiro/, README has stale info | Fix within session |
| STALE | Examples outdated (still valid but old format) | Fix next maintenance pass |
| COSMETIC | Formatting inconsistencies, missing dates | Low priority |

## Done Criteria

- [ ] All checks 1-19 pass
- [ ] Idempotency test passes (`just build && just build && git diff --exit-code .kiro/`)
- [ ] Validation script exists and runs clean
- [ ] project-hygiene agent can be invoked and produces structured report
- [ ] No BLOCKING or DRIFT findings remain
- [ ] Process documented for ongoing use
- [ ] examples/ generated and checks 20-23 pass (final step)
