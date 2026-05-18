# Spec: Phase 1 — Data Separation

**Status:** Planned  
**Date:** 2026-05-13  
**Depends on:** Phase 2, Phase 3 (generation must work before separating data)

## Objective

Separate personal user data from the published open-source project. After this phase, no personal project names, deployment outputs, or private config appear in committed files.

This ships as part of a single squash commit with all other phases — no intermediate state.

## Changes to .gitignore

Add these lines:

```gitignore
# User fleet data (personal projects)
fleet.yaml
projects/
```

`fleet.local.yaml` is already gitignored. No change needed there.

## Create fleet.example.yaml

A committed reference file showing the fleet.yaml format with fictional projects.

```yaml
# fleet.example.yaml — Reference configuration
# Copy to fleet.yaml and customize for your projects.

defaults:
  persona: personal
  crews: [general]
  theme: null
  components:
    signaling: standard
    sanity_gate: assumption-register
    search:
      variant: layered
      sources: [local, web]
      priority: "local → web"
      conflict: first-authoritative
    memory:
      variant: four-tier
      tiers: [working, session]
      discovery: false
    notifications:
      variant: channels
      channels: [toast]
      policy: completions
    task_tracking:
      variant: soft-hard
      backend: todo-tool
    decisions: progressive
    handoff: scope-based
    narration: verified
    troubleshooting:
      variant: systematic
      escalation:
        same_approach: 2
        strategies: 3
        action: ask-user
    writing:
      variant: standard
      editor:
        triggers: [new-document, significant-revision, user-facing]
      theme: null
    verification:
      variant: gate
      checks:
        build: null
        test: null
        lint: null
    git:
      variant: checkpoint
      worktrees: false
    completion:
      variant: standard
      followups: file-issues

projects:
  # agent-crews itself (self-hosted)
  agent-crews:
    crews: [meta]
    theme: null
    self_hosted: true
    components:
      verification:
        checks:
          build: "python generate.py --dry-run"
          test: "python -m pytest tests/"
          lint: null
      git:
        variant: checkpoint

  # Example: Rust CLI project
  ferris-tracker:
    crews: [general, bug-fix]
    theme: null
    components:
      verification:
        checks:
          build: "cargo check"
          test: "cargo test"
          lint: "cargo clippy"
      git:
        variant: pr-based

  # Example: Node/TypeScript web app
  taskflow-ui:
    persona: solutions-architect
    crews: [general, infrastructure]
    theme: wow
    components:
      verification:
        checks:
          build: "npm run build"
          test: "npm test"
          lint: "npx eslint ."
      notifications:
        channels: [toast, slack]
        slack_channel: "C0EXAMPLE"
        slack_channel_name: "#project-dev"

  # Example: Godot game project
  pixel-dungeon:
    type: custom
    crews: [general, content]
    theme: null
    components:
      verification:
        checks:
          build: "godot --headless --check-only"
          test: "godot --headless --run-tests"
          lint: null
```

## Update README

- Replace references to `fleet.yaml` with `fleet.example.yaml`
- Add "Getting Started" section: copy fleet.example.yaml → fleet.yaml, customize, run `just build`
- Remove any mention of specific personal projects

## Migration Steps

1. Ensure `fleet.yaml` and `projects/` are not modified (clean working tree)
2. Add `fleet.yaml` and `projects/` to `.gitignore`
3. `git rm --cached fleet.yaml` (removes from index, keeps local file)
4. `git rm --cached -r projects/` (removes from index, keeps local files)
5. Create `fleet.example.yaml` (as above)
6. Update README.md
7. Verify: `git status` shows fleet.yaml and projects/ as untracked (ignored)

**Note:** Git history still contains personal data. This is acceptable — the goal is forward-looking cleanliness, not history rewriting.

**Note:** `examples/` generation happens after Phase 5 as the final step. Not part of this phase.

## Verification: Done Criteria

- [ ] `git show HEAD:fleet.yaml` fails (file not in index)
- [ ] `git show HEAD:projects/` fails (directory not in index)
- [ ] `cat .gitignore | grep fleet.yaml` succeeds
- [ ] `cat .gitignore | grep projects/` succeeds
- [ ] `fleet.example.yaml` exists, is valid YAML, contains no personal project names
- [ ] `fleet.example.yaml` uses `persona: personal` as default
- [ ] `fleet.example.yaml` contains no real Slack channel IDs or personal paths
- [ ] README.md references fleet.example.yaml, not fleet.yaml
- [ ] Local `fleet.yaml` still works: `just build` succeeds
- [ ] No personal project names in any committed file (run scripts/validate.sh)
