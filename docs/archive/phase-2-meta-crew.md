# Spec: Phase 2 — Meta Crew

**Status:** Planned  
**Date:** 2026-05-13  
**Execution order:** First. This is the foundation all other phases build on.

## Objective

Define agent-crews' own crew as a crew YAML (`base/crews/meta.yaml`). This is the crew that maintains THIS repository — not a generic crew deployed to other projects.

Since all phases ship together in a single commit, `meta.yaml` existence is guaranteed when `fleet.example.yaml` references `crews: [meta]`. No special handling needed.

## File

`base/crews/meta.yaml`

## How Meta Differs from Hygiene

| Aspect | `hygiene.yaml` | `meta.yaml` |
|--------|----------------|-------------|
| Purpose | Maintain deployed target projects | Maintain agent-crews itself |
| Scope | Doc rot, deps, links, structure in any project | Crew design, generation pipeline, data separation, examples |
| Deployed to | Every project that opts in | agent-crews only |
| Agents | doc-checker, deps-checker, structure-checker, link-checker, fix-verifier | crew-creator, crew-augmenter, crew-doctor, crew-analyst, crew-researcher, kiro-helper, project-hygiene |
| "General crew always included" | Applies (hygiene is additive) | Does NOT apply — meta IS the general crew for agent-crews |

## Agent Roster

| Name | Type | Role |
|------|------|------|
| `dispatcher` | orchestrator | Routes work to the right specialist. Entry point for all tasks. |
| `crew-creator` | worker | Creates new crew YAMLs from scratch |
| `crew-augmenter` | worker | Adds agents/prompts to existing crews |
| `crew-doctor` | worker | Diagnoses and fixes crew issues |
| `crew-analyst` | worker | Analyzes crew quality, coverage, gaps |
| `crew-researcher` | worker | Investigates patterns, prior art, best practices |
| `kiro-helper` | worker | Kiro platform questions, agent JSON format, steering mechanics |
| `project-hygiene` | worker | **NEW** — repo health, data separation, doc accuracy |

## project-hygiene Agent

Responsibilities:

1. **README/AGENTS.md accuracy** — Verify docs match actual state. Fix drift.
2. **Doc separation enforcement** — User docs (README, use-case-guide, examples/) contain no internal details. Maintainer docs (specs, decisions, AGENTS.md) don't leak into user-facing paths.
3. **Data sanitization auditing** — No personal project names in committed files. fleet.yaml is gitignored. projects/ is gitignored. No Slack channel IDs, personal paths, or private config in committed code.
4. **Example curation** — examples/ directory exists, contains valid generated output, is instructive for new users.

Prompt excerpt:

```yaml
- name: project-hygiene
  description: "[Meta] Repo hygiene — data separation, doc accuracy, sanitization"
  routes: "Need repo health check, data separation audit, doc accuracy verification"
  prompt: |
    You are project-hygiene — you maintain the agent-crews repo itself.

    ## Your Checks
    1. Data separation: fleet.yaml and projects/ are gitignored. No personal
       project names appear in committed files.
    2. Doc accuracy: README references fleet.example.yaml. AGENTS.md matches
       .kiro/agents/*.json. No broken internal links.
    3. Doc separation: User docs contain no internal implementation details.
       Maintainer docs are clearly separated.
    4. Examples: examples/ exists with at least 2 reference projects.

    ## Output Format
    [SEVERITY] description
    File: path/to/file
    Fix: what needs to change

    Severities: BLOCKING > STALE > DRIFT > COSMETIC
    Fix BLOCKING and DRIFT directly. Report STALE and COSMETIC.
```

## Archetype Structure

```yaml
architypes:
  - type: orchestrator
    agents:
      - name: dispatcher
        description: "[Meta] Orchestrator — routes work to crew specialists"
        keyboardShortcut: ctrl+shift+d
        routes: "Entry point for all agent-crews work"

  - type: worker
    agents:
      - name: crew-creator
      - name: crew-augmenter
      - name: crew-doctor
      - name: crew-analyst
      - name: crew-researcher
      - name: kiro-helper
      - name: project-hygiene
```

## Prompt Definitions

Prompts are separate `.md` files in `.kiro/prompts/` (same convention as all other crews — no crew YAML has a prompts section). The generator syncs these from `shared/prompts/`. These prompts must exist for agent-crews:

| Prompt | Purpose |
|--------|---------|
| `grill-me` | Challenge a crew design with hard questions |
| `create-crew` | Guided workflow to create a new crew from scratch |
| `deploy-crew` | Generate and deploy a crew to a project |
| `crew-sheet` | Display all agents, crews, and routing |
| `review-crew-quality` | Deep quality audit of a crew YAML |
| `review-session` | Review a completed work session for improvements |
| `review-crew` | Quick review of crew structure and coverage |
| `tune-crew` | Iterative refinement of an existing crew |

## Implementation Notes

- Extract current hand-crafted agent prompts from `.kiro/agents/*.json` into crew YAML format
- Extract current prompt content from `.kiro/prompts/*.md` into the prompts section
- The meta crew YAML becomes the source of truth; hand-crafted JSON files become generated output
- project-hygiene is the only net-new agent — all others already exist
- Crew YAML follows same structure as `base/crews/hygiene.yaml` (workflow, scope, tools, architypes)
- Prompts remain as separate `.md` files in `.kiro/prompts/` (not embedded in crew YAML)
