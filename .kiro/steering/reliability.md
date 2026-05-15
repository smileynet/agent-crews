---
inclusion: always
---

# Reliability Protocol

## Validation Pipeline

After any crew modification (YAML, component, steering, skill):
1. Run `just build` — generation must succeed
2. Verify no drift between source and generated output
3. If agent behavior changed, recommend re-running affected evals

## Changelog Discipline

For user-facing changes, update CHANGELOG.md `[Unreleased]` in the same commit.

**Decision test:** User-facing = changes what deployers can do, how they do it, or fixes something broken.
Not user-facing = refactors, tests, internal tooling, steering tweaks.

**Quality rules (MANDATORY):**
- Write what users can now DO, not what was built internally
- If you can't write the entry without naming a file or function, it's not user-facing
- Technology-replacement test: would this entry still be true if the tech changed? If not, rewrite it
- ✅ "Deploy agent teams to any project with one command"
- ❌ "Generator produces .kiro/agents/*.json from crew YAML"

## Enforcement Hierarchy

1. Tool permissions (strongest — agent physically cannot do forbidden action)
2. Automated validation (crew-validator checks after changes)
3. Verification gate (verifier checks before completion)
4. Steering guidance (weakest — shapes behavior but can be overridden)

Never rely on a weaker mechanism when a stronger one is available.
