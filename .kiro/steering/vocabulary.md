---
inclusion: always
---

# Vocabulary

Canonical vocabulary for agent-crews. Use these exact keywords in scope definitions, routing, and documentation.

## Intent Keywords (handles/refuses)

These are the normalized keywords used in crew `scope.handles` and `scope.refuses` fields. Always use the canonical form.

| Canonical keyword | Meaning | Owned by crew |
|-------------------|---------|---------------|
| features | New functionality, feature work | general |
| mixed-work | Cross-cutting tasks, general requests | general |
| implementation | Code writing, building | general |
| refactoring | Code restructuring without behavior change | general |
| bugs | Bug fixing, debugging, test failures | bug-fix |
| testing | Test writing, test coverage | bug-fix |
| debugging | Root-cause analysis, troubleshooting | bug-fix |
| infrastructure | Provisioning, IaC, cloud resources | infrastructure |
| deployment | Deploy pipelines, CI/CD | infrastructure |
| ci-cd | CI/CD configuration | infrastructure |
| research | Investigation, analysis, prior art | research |
| documentation | Technical docs, knowledge capture | research, writing |
| writing | Prose composition, editing | writing |
| editing | Review, revision, style enforcement | writing |
| presentations | Slides, talks, visual content | content |
| tutorials | Educational content, workshops | content |
| project-hygiene | Maintenance, cleanup, tech debt | hygiene |
| brownfield-onboarding | Codebase mapping, architecture discovery | onboarding |

### Retired keywords (do NOT use)

| Retired | Use instead | Why |
|---------|-------------|-----|
| bug-fixing | bugs | Normalize to noun form |
| research-only | research | Drop unnecessary suffix |
| documentation-only | documentation | Drop unnecessary suffix |
| code-implementation | implementation | Drop redundant prefix |

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|----------|
| Crew workflow name | lowercase single word | `general`, `bug-fix`, `writing` |
| Agent name | kebab-case, role-descriptive | `general-lead`, `test-writer` |
| Skill file | kebab-case.md or SKILL.md in directory | `diagnose-crew.md`, `write-skill/SKILL.md` |
| Intent keyword | lowercase, hyphenated if multi-word | `mixed-work`, `ci-cd` |
| Component name | snake_case | `sanity_gate`, `task_tracking` |

## Scope Rules

- `handles`: what this crew actively works on
- `refuses`: what this crew explicitly will NOT do (must use canonical keywords)
- A crew only refuses an intent when a sibling crew is present to handle it
- The general crew is ALWAYS included — specialized crews add to it, never replace it
- Refused keywords must exactly match a sibling crew's handles keywords
