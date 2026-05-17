---
name: docs-audit
description: "Audit project documentation for quality, completeness, and freshness. Use when assessing documentation health, planning cleanup, or measuring improvement."
---

# Documentation Audit

## D.O.C.S. Anti-Pattern Framework

Four failure modes, ordered by developer impact:

### 1. Omission (blocks users entirely)
- [ ] README exists and is non-trivial
- [ ] Quick start / getting started exists
- [ ] Installation prerequisites documented
- [ ] Contributing guide exists
- [ ] Architecture overview for contributors
- [ ] License stated

### 2. Drift (breaks trust on contact)
- [ ] README describes what actually exists (not aspirational)
- [ ] Commands in docs produce expected output
- [ ] Referenced files and paths exist
- [ ] Version numbers are current

### 3. Confusion (increases time-to-value)
- [ ] Clear navigation structure
- [ ] No jargon without definition
- [ ] Code examples are runnable (not pseudocode)
- [ ] No wall of text before first actionable content
- [ ] Audience is clear (not mixing readers)

### 4. Stagnation (long-term decay)
- [ ] Docs updated within last 90 days
- [ ] No TODO/FIXME older than 30 days
- [ ] No "coming soon" that never came
- [ ] Docs for removed features deleted

## README Maturity Model

| Level | Name | Characteristics |
|:-----:|------|----------------|
| 1 | Code is the docs | No README |
| 2 | Bare minimum | Basic install, untested |
| 3 | Basic README | Setup works, some contributing info |
| 4 | README with purpose | Tested instructions, error guidance, roadmap |
| 5 | Product-oriented | Visuals, troubleshooting, weekly updates |

Target: Level 4 for internal projects, Level 5 for public/OSS.

## Severity (fix in this order)

| Severity | Definition | Example |
|----------|-----------|---------|
| BLOCKING | Prevents starting | No install instructions |
| STALE | Actively misleads | README describes removed feature |
| DRIFT | Partially wrong | Outdated version numbers |
| COSMETIC | Presentation | Formatting inconsistency |

## Scope

Audit documentation artifacts ONLY. Not code quality, test coverage, or dependencies.
