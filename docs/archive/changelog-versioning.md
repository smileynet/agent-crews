# Spec: Changelog & Versioning

**Status:** Planned
**Date:** 2026-05-15

## 1. Overview

This spec defines how agent-crews tracks changes, communicates value to users, and cuts releases. It covers:

- Semantic versioning model for the repo's public API surfaces
- Changelog format and entry quality standards
- Release tooling (`scripts/release.py`, `just release`, `just publish`)
- New meta-team agents (crew-validator, crew-releaser)
- Component design for changelog discipline in deployed projects
- Deployment scaffolding for project-level release infrastructure

**Why this exists:** Agent-crews is a publishable open-source project. Users need to understand what changed between versions without reading commit logs. Agents need enforceable rules about documenting their changes. The changelog is the contract between the project and its users.

**Core principle:** High reliability is the product value. Every design decision favors reliability over speed. Enforcement over suggestion — if something must happen, make it structurally impossible to skip.

---

## 2. Design Decisions

| # | Decision | Rationale |
|---|----------|----------|
| 1 | Repo URL: `https://github.com/smileynet/agent-crews` | From git remote |
| 2 | Backfill 0.1.0 with today's major changes | Gives first release substance, demonstrates format |
| 3 | Tag 0.1.0 after Phase 1 implementation | First release is self-documenting, includes its own changelog infrastructure |
| 4 | `just release` local by default, `--push` flag to auto-push | Safe default, configurable for those who want one-shot |
| 5 | Hard block release if Unreleased is empty | Prevents changelog rot, cheap enforcement |
| 6 | Dedicated skill + CONTRIBUTING.md update | Skill has full quality rules/examples; CONTRIBUTING.md references it for human contributors |
| 7 | Skill loaded by crew-validator only, with strong guidance to run after augmenter | Separation of concerns; validator checks what others create |
| 8 | New agent: crew-validator (separate from crew-doctor) | Doctor = reactive diagnosis/fix; Validator = proactive post-change verification |
| 9 | Validator scope: full post-change validation + eval recommendation | Changelog, build, schema, structural invariants, drift, and recommends eval re-runs for behavior changes |
| 10 | Auto-chain augmenter → validator by default, skippable | High reliability is the product value; validation is not optional overhead |
| 11 | Verifier checks for changelog entry in deployed projects; entry goes in [Unreleased] | Verification layer catches missing entries; entries accumulate until release |
| 12 | `@release` prompt + crew-releaser agent | Prompt is the manual trigger; agent orchestrates the full release pipeline (checks, curation, bump, tag) |
| 13 | High reliability principle documented in AGENTS.md + steering + ADR | AGENTS.md = discoverable; steering = operational; ADR = formal decision record |
| 14 | Standard variant = steering + verifier check; `changelog: null` bypasses entirely | Active enforcement when opted in; explicit off switch for projects that don't need it |
| 15 | crew-releaser tools: subagent + shell + read + write; git-host agnostic | Needs file editing for changelog curation + minor clarity edits; supports GitHub, GitLab, custom git |
| 16 | `just release` = universal (tag); `just publish` = platform-specific; agent detects available CLIs | Portable core; agent selects gh/glab/skip based on environment detection |
| 17 | Component = entry discipline only; crew-creator scaffolds release tooling during setup | Component enforces writing; release infrastructure is project-level, scaffolded at crew creation time |
| 18 | Python script for release (`scripts/release.py` via uv run) | Robust CHANGELOG.md parsing; consistent with existing scripts |
| 19 | Deployment setup phase: detect existing release tooling, scaffold if missing | Ensures agent instructions reference valid commands; same pattern as project.md skeleton |
| 20 | crew-creator scaffolds interactively; generator validates on subsequent builds | First-time = interactive setup; ongoing = automated health check with warning |

---

## 3. Semver Model

### Starting Version

`0.1.0` — initial release. The `0.x` prefix signals pre-1.0 instability per semver spec.

### Public API Surfaces

agent-crews exposes multiple "API" surfaces that users depend on:

| Surface | What users depend on | Breaking = MAJOR bump |
|---------|---------------------|----------------------|
| Generated agent JSON schema | Agent file structure, field names | Removing/renaming fields |
| Component YAML format | Component file structure, placeholder syntax | Changing `{{}}` syntax, removing fields |
| fleet.yaml schema | Project configuration keys | Removing/renaming config keys |
| CLI interface (`just` recipes) | Recipe names, argument order | Renaming recipes, changing arg semantics |
| Crew definitions | Agent names, roles, routing | Removing agents, changing delegation paths |
| Shared skills format | SKILL.md structure, loading conventions | Changing load mechanism |

### Version Bump Rules

| Change Type | Bump | Examples |
|-------------|------|----------|
| Breaking schema/format change | MAJOR | Remove a fleet.yaml key, change component YAML structure |
| New crew, agent, component, or feature | MINOR | Add writing crew, add changelog component, new `just` recipe |
| Bug fix, doc improvement, internal refactor | PATCH | Fix generator edge case, clarify steering, fix broken link |

### Pre-1.0 Semantics

While at `0.x.y`:
- MINOR bumps may include breaking changes (per semver spec)
- PATCH bumps must remain non-breaking
- Document breaking changes prominently in changelog under `### Changed` or `### Removed`

### Version Location

Single source of truth: `version.txt` file at repo root (plain text, one line, e.g. `0.1.0`).

---

## 4. Changelog Format

### Standard: Keep a Changelog 1.1.0

File: `CHANGELOG.md` at repo root.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Entry here

## [0.1.0] - 2026-05-15

### Added
- Entry here

[Unreleased]: https://github.com/smileynet/agent-crews/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/smileynet/agent-crews/releases/tag/v0.1.0
```

### Categories (in order)

| Category | When to use |
|----------|-------------|
| `Added` | New features, agents, components, crews |
| `Changed` | Behavior changes to existing features |
| `Deprecated` | Features marked for future removal |
| `Removed` | Features removed in this release |
| `Fixed` | Bug fixes |
| `Security` | Vulnerability fixes |

### Entry Quality Rules

**Core principle:** "The implementation is yours. The impact is theirs."

Every entry must pass these tests:

#### 1. Technology-Replacement Test

> If you replaced the underlying technology, would the entry still be true?

- ❌ `Added YAML parsing for component variants`
- ✅ `Added variant selection — projects can now choose between standard and minimal changelog enforcement`

#### 2. Can't-Name-a-File Heuristic

> If the entry could be replaced by a filename, it's too low-level.

- ❌ `Updated shared/components/changelog/standard.yaml`
- ✅ `Added changelog discipline component — agents are reminded to document changes as they work`

#### 3. Impact Over Mechanism

> Describe what users can now do, not what the code does.

- ❌ `Refactored generate.py to support component null bypass`
- ✅ `Projects can now opt out of changelog enforcement with `changelog: null` in fleet.yaml`

#### 4. One Entry Per User-Visible Change

> Group implementation details under a single entry. Don't list every file touched.

- ❌ Three entries: "Added release.py", "Added just release recipe", "Added just publish recipe"
- ✅ One entry: `Added release tooling — `just release` bumps version and tags; `just publish` creates platform release`

#### 5. Present Tense, Active Voice, No Period

> Consistent style across all entries.

- ❌ `The dispatcher was updated to route to the new validator agent.`
- ✅ `Add crew-validator agent — proactive post-change verification (changelog, schema, drift)`

### Good vs Bad Examples

**Bad entries (mechanism-focused):**
```markdown
- Updated dispatcher.json to include crew-validator routing
- Modified generate.py to handle changelog component
- Added new YAML file for changelog standard variant
- Fixed bug in release script where version wasn't bumped
```

**Good entries (impact-focused):**
```markdown
- Add crew-validator agent — proactive post-change verification catches missing changelog entries, schema violations, and structural drift
- Add changelog component — deployed projects get automatic reminders to document user-facing changes
- Add release pipeline — `just release` validates, bumps version, updates changelog, and tags in one command
- Fix release script failing silently when CHANGELOG.md has Windows line endings
```

---

## 5. Release Tooling

### `scripts/release.py`

Python script executed via `uv run scripts/release.py`. Inline dependencies (no requirements.txt needed).

**Behavior:**

```
uv run scripts/release.py [--bump major|minor|patch] [--push] [--dry-run]
```

1. **Validate preconditions:**
   - `CHANGELOG.md` exists
   - `[Unreleased]` section is non-empty (hard block if empty — Decision #5)
   - Working tree is clean (`git status --porcelain` is empty)
   - Current branch is `main`

2. **Determine version:**
   - Read current version from `version.txt` file
   - Apply bump (default: `minor` for new features, `patch` for fixes)
   - If `--bump` not specified, infer from changelog categories:
     - Has `Removed` or `Changed` → suggest `major` (confirm interactively)
     - Has `Added` → `minor`
     - Only `Fixed`/`Security` → `patch`

3. **Update files:**
   - Replace `## [Unreleased]` content → move to `## [X.Y.Z] - YYYY-MM-DD`
   - Add empty `## [Unreleased]` section above
   - Update comparison links at bottom of file
   - Write new version to `version.txt` file

4. **Commit and tag:**
   - `git add CHANGELOG.md version.txt`
   - `git commit -m "release: vX.Y.Z"`
   - `git tag -a vX.Y.Z -m "Release X.Y.Z"`

5. **Push (if `--push` flag):**
   - `git push origin main`
   - `git push origin vX.Y.Z`

6. **Dry-run mode:** Print what would happen without modifying anything.

**Exit codes:**
- `0` — success
- `1` — precondition failure (empty unreleased, dirty tree, wrong branch)
- `2` — user cancelled

### `just release`

```just
# Cut a release (local by default)
release *args:
    uv run scripts/release.py {{args}}
```

Usage:
- `just release` — interactive, local only
- `just release --bump minor` — explicit bump, local only
- `just release --push` — release and push tags + commits
- `just release --dry-run` — preview without changes

### `just publish`

Platform-specific release creation. Separate from `just release` (Decision #16).

```just
# Create platform release (GitHub/GitLab) from latest tag
publish:
    #!/usr/bin/env bash
    set -e
    TAG=$(git describe --tags --abbrev=0)
    VERSION=${TAG#v}
    # Extract this version's changelog section
    NOTES=$(uv run scripts/release.py --extract-notes "$VERSION")
    if command -v gh &>/dev/null; then
        gh release create "$TAG" --title "$VERSION" --notes "$NOTES"
    elif command -v glab &>/dev/null; then
        glab release create "$TAG" --name "$VERSION" --notes "$NOTES"
    else
        echo "No platform CLI found (gh, glab). Tag $TAG exists — create release manually."
        echo ""
        echo "$NOTES"
    fi
```

### Validation Rules (enforced by script)

| Check | Failure mode |
|-------|-------------|
| `[Unreleased]` is empty | Hard block — cannot release (Decision #5) |
| Working tree dirty | Hard block — commit or stash first |
| Not on `main` branch | Hard block — switch to main |
| version.txt file missing | Create with `0.0.0`, then bump |
| Malformed changelog | Error with line number and description |

---

## 6. Meta Team Changes

### New Agent: crew-validator

**Purpose:** Proactive post-change verification. Runs after any modification to catch issues before they compound.

**Separation from crew-doctor:** Doctor is reactive (user reports a problem → diagnose → fix). Validator is proactive (change happened → verify everything still holds).

**Scope (Decision #9):**
- Changelog entry exists for user-facing changes
- `just build` produces clean output (no warnings, no drift)
- Schema validation passes for all modified agents
- Structural invariants hold (general crew always included, no orphan agents)
- Component drift detection (fleet.yaml ↔ generated output)
- Recommends eval re-runs when behavioral changes detected

**Configuration:**

```json
{
  "name": "crew-validator",
  "description": "Proactive post-change verification — changelog, schema, drift, structural invariants",
  "role": "worker",
  "tools": ["read", "shell", "write", "summary"],
  "allowedCommands": ["just build", "just check", "just validate *", "git diff *", "git status *", "uv run generate.py --dry-run"],
  "skills": ["shared/skills/changelog-discipline/SKILL.md"],
  "resources": ["CHANGELOG.md", "version.txt", "fleet.example.yaml"]
}
```

**Routing:** Dispatcher routes to crew-validator when:
- User says "validate", "check my changes", "did I break anything"
- Auto-chained after crew-augmenter completes (Decision #10)

### New Agent: crew-releaser

**Purpose:** Orchestrates the full release pipeline — validates readiness, curates changelog, bumps version, tags, optionally publishes.

**Configuration:**

```json
{
  "name": "crew-releaser",
  "description": "Release pipeline orchestrator — validates, curates changelog, bumps version, tags, publishes",
  "role": "worker",
  "tools": ["read", "write", "shell", "subagent", "summary"],
  "allowedCommands": ["just release *", "just publish", "just build", "just check", "git *", "uv run scripts/release.py *"],
  "skills": ["shared/skills/changelog-discipline/SKILL.md"],
  "resources": ["CHANGELOG.md", "version.txt", "docs/specs/changelog-versioning.md"]
}
```

**Routing:** Dispatcher routes to crew-releaser when:
- User says "release", "cut a release", "tag a version"
- User invokes `@release` prompt

**Workflow:**
1. Run `just check` — abort if health issues
2. Read `CHANGELOG.md` — verify `[Unreleased]` is non-empty
3. Review entries for quality (technology-replacement test, impact focus)
4. Suggest minor edits for clarity (user approves)
5. Determine version bump (infer from categories or ask)
6. Execute `just release --bump <type>`
7. Ask if user wants `just publish`

### Dispatcher Routing Updates

Add to dispatcher's routing table:

```
"validate changes" | "check my work" | "verify" → crew-validator
"release" | "cut release" | "tag version" | "publish" → crew-releaser
```

### Auto-Chain Pattern (Decision #10)

When crew-augmenter completes a task, it includes in its summary:

```
⚡ Validation recommended. Run `/agent crew-validator` or say "validate" to verify changes.
```

The dispatcher, upon receiving augmenter's completion summary, automatically suggests validation. The user can skip with "skip validation" or proceed by default.

Implementation: Add to crew-augmenter's completion steering:

```markdown
## Post-Completion
After completing any modification to crew files, components, or skills:
1. Report what was changed
2. Append: "⚡ Recommend running crew-validator to verify. Say 'validate' or 'skip'."
```

### New Skill: `shared/skills/changelog-discipline/SKILL.md`

Loaded by: crew-validator only (Decision #7).

Content covers:
- Entry quality rules (all 5 tests from Section 4)
- When an entry is required vs optional
- Where entries go (`[Unreleased]` section)
- Category selection guidance
- Examples of good/bad entries

**When an entry is required:**
- Any change to crew definitions (new agent, removed agent, changed routing)
- Any change to components (new variant, changed behavior)
- Any change to fleet.yaml schema
- Any change to `just` recipes
- Any new/changed skill that affects agent behavior
- Bug fixes that users would notice

**When an entry is NOT required:**
- Internal refactoring with no behavior change
- Test-only changes
- CI/tooling changes invisible to users
- Typo fixes in internal docs

---

## 7. Component Design

### Purpose

The changelog component enforces **entry discipline** in deployed projects (Decision #17). It does NOT provide release tooling — that's scaffolded by crew-creator at setup time.

### `shared/components/changelog/standard.yaml`

```yaml
name: changelog-standard
description: "Changelog entry discipline — agents document user-facing changes as they work"

targets: [worker]

prompt: ""

allowed_commands: []

resources: []
hooks: {}

steering: |
  ---
  inclusion: always
  ---
  # Changelog Discipline

  **After completing any user-facing change, add an entry to CHANGELOG.md under `## [Unreleased]`.**

  ## When to Add an Entry

  Add an entry when your change:
  - Adds a feature users will notice
  - Changes existing behavior
  - Fixes a bug users could hit
  - Removes something users depended on
  - Fixes a security issue

  Do NOT add an entry for:
  - Internal refactoring (no behavior change)
  - Test-only changes
  - CI/tooling invisible to users

  ## Entry Format

  ```markdown
  ### Added|Changed|Deprecated|Removed|Fixed|Security
  - <Impact-focused description starting with verb>
  ```

  ## Quality Rules

  1. **Technology-replacement test:** Would the entry still be true if you swapped the tech?
  2. **Can't-name-a-file:** If the entry is just a filename, rewrite it
  3. **Impact over mechanism:** Describe what users can do, not what code does
  4. **Present tense, active voice, no trailing period**

  ## Procedure

  1. Complete your implementation
  2. Determine if the change is user-facing (apply the tests above)
  3. If yes: add entry under the correct category in `## [Unreleased]`
  4. If the `## [Unreleased]` section doesn't exist, create it below the header

subagents: []
```

### `shared/components/changelog/pr-review.yaml`

For projects using PR-based git workflow — adds changelog check to PR review criteria.

```yaml
name: changelog-pr-review
description: "PR review checks for changelog entries — reviewer verifies entry exists and meets quality bar"

targets: [orchestrator]

prompt: ""

allowed_commands: []

resources: []
hooks: {}

steering: |
  ---
  inclusion: always
  ---
  # PR Review: Changelog Check

  When reviewing a PR, verify:

  1. **Entry exists** (if change is user-facing)
     - Check `## [Unreleased]` section in CHANGELOG.md
     - If missing and change is user-facing: request entry before approval

  2. **Entry quality** (apply all tests)
     - Technology-replacement test passes
     - Not just a filename
     - Describes impact, not mechanism
     - Correct category (Added/Changed/Fixed/etc.)
     - Present tense, active voice

  3. **Entry placement**
     - Under `## [Unreleased]`, not under a versioned heading
     - Under the correct category heading

  If entry is missing or low-quality, request changes with specific feedback.

subagents: []
```

### fleet.yaml Integration

Add `changelog` to the defaults section:

```yaml
defaults:
  components:
    changelog:
      variant: standard    # standard | pr-review | null
```

Per-project override:

```yaml
projects:
  my-project:
    components:
      changelog:
        variant: pr-review   # PR-based projects get review checks

  scratch-project:
    components:
      changelog: null        # Explicitly opt out (Decision #14)
```

### Null Bypass (Decision #14)

When `changelog: null` is set for a project:
- Generator skips the changelog component entirely
- No steering file written
- No verifier check for changelog entries
- Project operates as if changelog component doesn't exist

This is the explicit off-switch for projects that don't need changelog discipline (scratch projects, experiments, forks).

---

## 8. Deployment Setup

### crew-creator Scaffolding Workflow (Decision #19, #20)

When crew-creator sets up a new project, it includes a release infrastructure step:

**Detection phase:**
1. Check if `CHANGELOG.md` exists in target project
2. Check if `version.txt` file exists
3. Check if justfile has `release` recipe
4. Check if git tags exist with semver pattern

**Scaffolding (interactive — Decision #20):**

```
Detected: No changelog infrastructure.

I'll set up:
  ✓ CHANGELOG.md (Keep a Changelog format)
  ✓ version.txt file (starting at 0.1.0)
  ✓ Release recipes in justfile (just release, just publish)
  ✓ scripts/release.py (version bump + tag)

Proceed? [Y/n]
```

If user declines: set `changelog: null` in fleet.yaml for that project.

**What gets created:**

| File | Content |
|------|---------|
| `CHANGELOG.md` | Template with `[Unreleased]` section |
| `version.txt` | `0.1.0` (or detected from existing tags) |
| `justfile` additions | `release` and `publish` recipes |
| `scripts/release.py` | Copy from agent-crews template (adapted for project) |

**If infrastructure already exists:**
- Detect and respect existing format
- Only add missing pieces
- Never overwrite existing CHANGELOG.md content

### Generator Validation (Decision #20)

On subsequent `just build` runs, the generator checks:

1. If `changelog` component is active (not null) for a project
2. Verify `CHANGELOG.md` exists in the project's deploy target
3. If missing: emit warning (not error)

```
⚠ Project 'my-project' has changelog component active but no CHANGELOG.md at deploy target.
  Run `just link my-project` after creating CHANGELOG.md, or set `changelog: null` to disable.
```

This is a warning, not a hard error — the project might not be deployed yet.

---

## 9. Documentation Deliverables

### ADR: High Reliability Principle

File: `docs/decisions/ADR-006-high-reliability.md`

```markdown
# ADR-006: High Reliability Principle

**Status:** Accepted
**Date:** 2026-05-15

## Context

agent-crews' value proposition is reliability — users trust that deployed agents
follow protocols consistently. This trust requires enforcement mechanisms, not
just documentation.

## Decision

1. Validation is mandatory after changes, not optional overhead
2. Enforcement via tool permissions and structural checks, not prompt suggestions
3. Auto-chain pattern: creation → validation by default
4. Changelog entries required for user-facing changes (enforced by component + verifier)

## Consequences

- New crew-validator agent for proactive verification
- Auto-chain from augmenter → validator
- Changelog component with hard enforcement (not soft reminders)
- `just release` blocks on empty [Unreleased] section
```

### AGENTS.md Update

Add to the agents table:

```markdown
| crew-validator | `/agent crew-validator` | Proactive post-change verification — changelog, schema, drift |
| crew-releaser | `/agent crew-releaser` | Release pipeline — validate, curate changelog, bump, tag, publish |
```

Add to prompts table:

```markdown
| `@release` | Cut a release — validate, curate, bump, tag |
```

### Steering File

File: `shared/steering/universal/high-reliability.md`

```markdown
---
inclusion: always
---
# High Reliability

This project values reliability over speed.

- Every change must be verifiable
- Validation is not optional overhead — it's the product
- If something must happen, it's enforced structurally (tool permissions, gates)
- If something should happen, it's documented in steering (guidance, not enforcement)
```

### CONTRIBUTING.md Update

Add a "Changelog" section:

```markdown
## Changelog

Every user-facing change needs a CHANGELOG.md entry under `## [Unreleased]`.

**What counts as user-facing:**
- New/changed/removed crews, agents, components, skills
- New/changed `just` recipes
- Bug fixes users would notice
- Schema changes to fleet.yaml or component format

**Entry format:** See `shared/skills/changelog-discipline/SKILL.md` for full rules.

**Quick version:** Describe impact, not mechanism. Present tense, active voice.
- ✅ `Add changelog component — agents document changes as they work`
- ❌ `Updated standard.yaml with new steering content`
```

### docs/operational-model.md

Add a "Release Process" section documenting:
- How releases are cut (`just release` → `just publish`)
- Version semantics (what's MAJOR/MINOR/PATCH)
- Who can release (anyone with push access to main)
- Release cadence (no fixed schedule — release when [Unreleased] has substance)

---

## 10. Implementation Phases

### Phase 1: Foundation (no dependencies)

**Deliverables:**
- `CHANGELOG.md` — backfilled with 0.1.0 content (Decision #2)
- `version.txt` — containing `0.1.0`
- `scripts/release.py` — full release script
- `just release` and `just publish` recipes in justfile
- `docs/decisions/ADR-006-high-reliability.md`

**Verification:**
- `just release --dry-run` succeeds
- Script correctly parses backfilled changelog
- Script blocks when `[Unreleased]` is empty

**Tag:** `v0.1.0` after this phase (Decision #3)

---

### Phase 2: Component System (depends on Phase 1)

**Deliverables:**
- `shared/components/changelog/standard.yaml`
- `shared/components/changelog/pr-review.yaml`
- `fleet.example.yaml` updated with `changelog` in defaults
- Generator updated to handle `changelog: null` bypass
- `shared/components/README.md` updated with changelog entry

**Verification:**
- `just build` generates changelog steering in project output
- Setting `changelog: null` produces no changelog steering
- Component README lists changelog variants

---

### Phase 3: Skill & Validation Agent (depends on Phase 2)

**Deliverables:**
- `shared/skills/changelog-discipline/SKILL.md`
- crew-validator agent definition in `base/crews/meta.yaml`
- Dispatcher routing update for validator
- Auto-chain guidance in crew-augmenter's completion steering

**Verification:**
- `just build` generates crew-validator in `.kiro/agents/`
- Dispatcher routes "validate" to crew-validator
- Skill file is < 100 lines (ADR-001 constraint)

---

### Phase 4: Release Agent & Prompt (depends on Phase 3)

**Deliverables:**
- crew-releaser agent definition in `base/crews/meta.yaml`
- `@release` prompt in `.kiro/prompts/release.md`
- Dispatcher routing update for releaser

**Verification:**
- `just build` generates crew-releaser in `.kiro/agents/`
- Dispatcher routes "release" to crew-releaser
- `@release` prompt exists and references correct workflow

---

### Phase 5: Documentation & Integration (depends on Phase 1-4)

**Deliverables:**
- AGENTS.md updated (new agents, new prompt)
- CONTRIBUTING.md updated (changelog section)
- `shared/steering/universal/high-reliability.md`
- `docs/operational-model.md` release process section
- crew-creator updated with scaffolding workflow

**Verification:**
- All internal links resolve
- AGENTS.md matches generated `.kiro/agents/*.json`
- `just ci` passes

---

### Phase 6: Deployed Project Support (depends on Phase 2, 5)

**Deliverables:**
- Generator validation (warn if changelog active but no CHANGELOG.md)
- crew-creator interactive scaffolding for new projects
- Template `scripts/release.py` for deployed projects (simplified version)

**Verification:**
- New project creation offers changelog setup
- Generator warns appropriately for missing CHANGELOG.md
- Template script works standalone in a fresh project

---

### Dependency Graph

```
Phase 1 (Foundation)
    │
    ├──→ Phase 2 (Components)
    │        │
    │        ├──→ Phase 3 (Skill + Validator)
    │        │        │
    │        │        └──→ Phase 4 (Releaser + Prompt)
    │        │                 │
    │        └─────────────────┤
    │                          │
    └──────────────────────────┴──→ Phase 5 (Docs)
                                        │
                               Phase 6 (Deploy Support)
```

---

## 11. Antipatterns

### What NOT to Do

| Antipattern | Why it fails | Do this instead |
|-------------|-------------|-----------------|
| **Auto-generate changelog from commits** | Commit messages are for developers; changelog is for users. Different audiences, different language. | Write entries manually with user-facing language |
| **One entry per commit** | Produces noise. Users don't care about 47 implementation steps. | One entry per user-visible change, regardless of commit count |
| **Changelog as afterthought** | Entries written at release time are low-quality — you've forgotten the context. | Write entries as you work (component enforces this) |
| **Version in multiple files** | Drift between sources. Which one is canonical? | Single `version.txt` file, everything reads from it |
| **Changelog in a non-standard location** | Tools can't find it, contributors don't know where to look. | Always `CHANGELOG.md` at repo root |
| **Custom format** | Every reader must learn your format. Tooling doesn't work. | Keep a Changelog 1.1.0 — widely understood, tooling-friendly |
| **Mixing user-facing and internal changes** | Dilutes signal. Users skip the changelog because it's full of noise. | Internal changes don't get entries. Period. |
| **Release without validation** | Broken releases destroy trust faster than features build it. | `just release` runs full validation before tagging |
| **Soft reminders instead of hard blocks** | "Please remember to..." is ignored under pressure. | Script refuses to release if `[Unreleased]` is empty |
| **Changelog entries that name files** | `Updated config.yaml` tells users nothing. | Describe the capability change, not the file change |
| **Skipping changelog for "small" changes** | Small changes accumulate. Users upgrade and find undocumented behavior changes. | If a user would notice, it gets an entry |
| **Releasing from non-main branch** | Creates confusion about what's released vs what's in progress. | Script enforces main-branch-only releases |
| **Force-pushing tags** | Breaks anyone who already pulled the tag. Tags are immutable. | If a release is bad, cut a new patch release |
| **Changelog entries written by the release agent** | Agent wasn't there when the change was made — entries will be mechanism-focused. | Entries written by the agent that made the change; releaser only curates |

### Red Flags in Entries

If you see these patterns, the entry needs rewriting:

- Starts with "Updated", "Modified", "Changed" + a filename
- Contains a function name, class name, or variable name
- Could apply to any project (too generic)
- Requires reading the diff to understand
- Is longer than two lines (probably multiple changes crammed together)
- Uses passive voice ("was added", "has been fixed")
