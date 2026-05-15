---
inclusion: always
---
# Verification Protocol

**Gate workflow (MANDATORY before reporting DONE):**
identify → run → read → verify → claim

1. **Identify** what checks apply to this task type
2. **Run** the checks (build, test, lint, etc.)
3. **Read** the output (don't assume pass from exit code alone)
4. **Verify** output confirms the work is correct
5. **Claim** completion only with fresh evidence

## Checks by Task Type

| Task Type | Required Checks |
|-----------|----------------|
| code | build, test, lint, scope |
| infrastructure | plan-review, scope |
| config | build, smoke |
| writing | editor, style-check, links, accuracy |
| research | sources, traceability, completeness |
| product_design | walkthrough, completeness, coherence, jtbd-alignment |
| architecture | assumptions, alternatives, consequences |
| ui_ux | spec-compliance, accessibility, responsive, states |
| deployment | health, smoke, logs |
| data_migration | integrity, before-after, rollback |
| testing | coverage, edge-cases, red-green |
| refactoring | behavior-preservation |
| planning | completeness, actionability, dependencies |
| security | threat-model, owasp, secrets, permissions |

## Project-Specific Commands
- Build: ``
- Test: ``
- Lint: ``

## Scope Check (always applies)
Run `git diff` — changes must be limited to the current task.
Unrelated changes = scope violation. Revert or split.

## Violations
These are NOT acceptable as verification:
- "Should pass" / "looks fine"
- "Agent reported success"
- Trusting a previous run without re-running
- Skipping checks because "it's a small change"
