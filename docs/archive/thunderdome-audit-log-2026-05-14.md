# Thunderdome Audit Log — 2026-05-14

All modifications from the public release readiness + thunderdome content audit, annotated with the ADR-005 rule that drove each action.

## Skills — Structural Changes

| Action | Item | Rule | Rationale |
|--------|------|------|-----------|
| CUT | `aws-architecture.md` | §9: Project-specific | AWS patterns for one user's stack, not generic |
| CUT | `deno-core-patterns.md` | §9: Project-specific | deno_core V8 embedding for a personal project only |
| CUT | `rust-gamedev-patterns.md` | §9: Project-specific | Rust ECS/tick patterns for a personal project only |
| CUT | `terraform-patterns.md` | §9: Project-specific | Terraform module conventions for one project |
| CUT | `prototype-workflow.md` | §9: Project-specific | Replaced with generic `spike-workflow.md` |
| CUT | `parallel-dispatch.md` | §9: Duplicates another | Restates what orchestrator prompts already say |
| CUT | `antipatterns.md` | §3: Anti-patterns live with their skill | Dissolved into coding-principles + code-review |
| MERGED | `git-conventions.md` → git component | §9: Duplicates another | Git component steering already covers commit format |
| MERGED | `docs-organization/` → `diataxis-classification/` | §9: Duplicates another | docs-organization literally referenced diataxis as its classifier |
| MERGED | `mermaid-limits/` → `diagrams/` | §9: Duplicates another | Mermaid limits are a subsection of the diagrams skill |
| ADDED | `spike-workflow.md` | §10: Actionable, clear trigger | Generic version of prototype-workflow (hypothesis → measure → decide) |
| WIRED | `kiro-cli-schema` → kiro-helper agent | §10: Referenced by agents | Was unreferenced due to wiring bug, not content problem |
| WIRED | `session-review-patterns` → crew-analyst agent | §10: Referenced by agents | Was unreferenced due to wiring bug, not content problem |
| RESTRUCTURED | `write-skill.md` → `write-skill/SKILL.md` + `references/` | §6: Four skill types | Now a living example of the multi-file pattern it documents |

## Skills — Content Trimming

| Action | Item | Before | After | Rule | What was cut |
|--------|------|:------:|:-----:|------|-------------|
| REWRITE | `diagrams/SKILL.md` | 258 | 77 | §7: Under 100 lines | Full Kroki format catalog (30+ formats), verbose examples |
| REWRITE | `diataxis-classification/SKILL.md` | 199 | 56 | §7: Under 100 lines | Textbook essay → concise decision tree. Merged placement from docs-organization |
| REWRITE | `document-formats/SKILL.md` | 179 | 45 | §7: Under 100 lines | Syntax examples agents don't need (AsciiDoc/RST/Typst boilerplate) |
| REWRITE | `ai-assisted-development.md` | 66 | 39 | §9: Purely explanatory | Philosophy tables → actionable checklist + verification steps |
| TRIM | `testing-patterns.md` | 131 | 52 | §4: Domain-specific uses lazy linking | Stack-specific boilerplate (CDK/Lambda/React) → one-liner hints |
| TRIM | `code-review.md` | 115 | 90 | §9: Duplicates another | Trust Boundary Rule (in antipatterns), Transform Safety (niche) |
| TRIM | `antipatterns.md` | 107 | — | §3: Dissolved | Content moved to coding-principles (§2: attention anchors) + code-review |
| TRIM | `docs-audit/SKILL.md` | 136 | 62 | §7: Under 100 lines | Output template (agent can format), sources section |
| TRIM | `kiro-cli-schema/SKILL.md` | 106 | 98 | §9: Duplicates another | Subagent tool table (already in session-review-patterns) |
| TRIM | `tutorial-authoring/SKILL.md` | 104 | 92 | §9: Duplicates another | Tutorial vs How-To table (in diataxis), sources |
| ADDED | antipatterns table to `coding-principles.md` | 92 | 106 | §2: Templates direct attention | 9 patterns as signal→fix anchors |
| ADDED | AI patterns + false positives to `code-review.md` | 74 | 90 | §2: Templates direct attention | AI-specific generation patterns + calibration |

## Components — Changes

| Action | Item | Rule | Rationale |
|--------|------|------|-----------|
| MERGED | signaling format → `completion/standard.yaml` | §9: Duplicates another | Signal format was step 3 of completion; having it separate meant loading two files for one workflow |
| TRIM | `completion/standard.yaml` | — | Removed secret handling (tangential to completion) |
| TRIM | `task-tracking/soft-hard.yaml` | §9: Duplicates another | Removed rubber-stamp guard (canonical home is sanity-gate) |
| TRIM | `task-tracking/soft-hard.yaml` | §9: Purely explanatory | Rewrote "Simulation-as-Validation" vague advice → concrete checklist |
| TRIM | `memory/four-tier.yaml` | §9: Duplicates another | Removed Aging section (redundant with tier table lifetime column) |
| TRIM | `decisions/progressive.yaml` | §9: Duplicates another | Removed Spec Process section (belongs in upfront variant only) |
| REMOVED | `signaling: standard` from fleet.example.yaml defaults | — | No longer a separate component; format lives in completion |

## Prompts — Changes

| Action | Item | Before | After | Rule | What was cut |
|--------|------|:------:|:-----:|------|-------------|
| REWRITE | `review-crew-quality.md` | 196 | 47 | §7: Under 100 lines | 196-line spec → 47-line prompt. Bash snippets and detailed tables don't belong in a prompt |
| TRIM | `review-crew.md` | 80 | 60 | §2: Templates direct attention | 30-line output template → 8-line structure hint. Trust the agent to format |
| ADDED | `thunderdome.md` | — | 23 | — | New prompt: ruthless feature audit |

## Sanitization (Public Release)

| Action | Item | Rule | Rationale |
|--------|------|------|-----------|
| REMOVED | Personal project names from 7 files | Data separation | Personal project names scrubbed from all tracked files |
| REMOVED | Internal tool references from 9 files | Data separation | Organization-specific tool references removed |
| REMOVED | Personal project memory file from git | Data separation | Personal project data tracked by mistake |
| REMOVED | Internal MCP server from example crew.yaml files | Data separation | Internal MCP server in public examples |
| ADDED | `.kiro/memory/` to .gitignore | Data separation | Prevent future memory files from being tracked |

## Community Infrastructure (New Files)

| Action | Item | Rationale |
|--------|------|-----------|
| ADDED | `.github/ISSUE_TEMPLATE/bug_report.yml` | YAML form with structured fields + validation |
| ADDED | `.github/ISSUE_TEMPLATE/bug_report_md.md` | Markdown template for agent/programmatic submissions |
| ADDED | `.github/ISSUE_TEMPLATE/feature_request.yml` | YAML form with category dropdown |
| ADDED | `.github/ISSUE_TEMPLATE/feature_request_md.md` | Markdown template for agent/programmatic submissions |
| ADDED | `.github/ISSUE_TEMPLATE/config.yml` | Enables blank issues, links to discussions |
| ADDED | `.github/pull_request_template.md` | Concise: Why + What changed + Verification checklist |
| ADDED | `SECURITY.md` | Response timeline (7d), 90-day disclosure, GitHub private reporting |
| ADDED | `docs/decisions/ADR-005-skill-design-principles.md` | Captures all skill design rules from this audit |

## Documentation Restructuring

| Action | Item | Rationale |
|--------|------|-----------|
| REWRITE | `README.md` | Progressive disclosure, removed Agents row (AGENTS.md is agent entry point) |
| REWRITE | `CONTRIBUTING.md` | First-contribution path first, multi-file skill docs, progressive disclosure |
| REWRITE | `SECURITY.md` | Google/OpenSSF best practices: timeline, supported versions, private reporting |

## Summary

| Category | Before | After | Net |
|----------|:------:|:-----:|:---:|
| Skills (files) | 28 | 22 | -6 |
| Skills (total lines) | ~2200 | ~1487 | -713 |
| Skills over 100 lines | 6 | 1 | -5 |
| Components | 14 | 14 | 0 (1 merged internally) |
| Prompts | 8 | 9 | +1 (thunderdome) |
| Context budget recovered | — | — | ~951 lines |
