# Spec: Phase 3 — Fleet Wiring + Generation

**Status:** Planned  
**Date:** 2026-05-13  
**Depends on:** Phase 2 (meta crew)

## Objective

Add agent-crews to its own fleet and generate `.kiro/` from the meta crew YAML. After this phase, `just build` produces the same agents that currently exist as hand-crafted JSON — or intentionally improved versions.

## Fleet Entry for agent-crews

In `fleet.example.yaml`:

```yaml
projects:
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
```

## Fleet Reading

The generator reads both fleet files. Since all phases ship together, both files are straightforward:

```python
def load_fleet():
    fleet = {}
    if Path('fleet.example.yaml').exists():
        fleet.update(load_yaml('fleet.example.yaml')['projects'])
    if Path('fleet.yaml').exists():
        fleet.update(load_yaml('fleet.yaml')['projects'])
    return fleet
```

`fleet.example.yaml` (committed) contains the `agent-crews` entry and example projects.  
`fleet.yaml` (local, gitignored) contains personal projects. Entries in `fleet.yaml` override on conflict.

A fresh clone can run `just build agent-crews` without any local config.

## Special Output Handling

Normal projects: `just build` → `projects/{name}/.kiro/`

agent-crews with `self_hosted: true`: `just build` → `.kiro/` at repo root.

```python
def output_dir(project_name, project_config):
    if project_config.get('self_hosted'):
        return Path('.')  # repo root
    return Path('projects') / project_name
```

## Idempotency Requirement

Generated crews MUST be idempotent from configs. Running `just build` twice with no config changes produces zero diff:

```bash
just build && just build && git diff --exit-code .kiro/
```

This must pass. No timestamps, random ordering, or non-deterministic output in generated files.

Implementation requirements:
- Sort agent JSON keys consistently
- Sort file output order deterministically
- No timestamps or generation metadata in output files
- Template rendering must be pure (same input → same output)

## Generate Command

```bash
just build              # all projects
just build agent-crews  # just this project
```

Both produce `.kiro/agents/*.json` and `.kiro/prompts/*.md` at the repo root.

## Verification

### Diff Test

```bash
# Snapshot current state
cp -r .kiro/ .kiro.handcrafted/

# Generate
just build agent-crews

# Compare
diff -r .kiro.handcrafted/agents/ .kiro/agents/
diff -r .kiro.handcrafted/prompts/ .kiro/prompts/
```

Expected outcomes:
- **Identical:** Meta crew YAML faithfully reproduces hand-crafted agents.
- **Intentional improvements:** Document what changed and why. Generated version becomes new baseline.
- **Regressions:** Fix meta crew YAML or generator until output is correct.

### Idempotency Test

```bash
just build agent-crews
just build agent-crews
git diff --exit-code .kiro/
```

Must exit 0. Run this as part of CI.

## Done Criteria

- [ ] `fleet.example.yaml` contains agent-crews entry with `self_hosted: true`
- [ ] Generator reads both fleet.example.yaml and fleet.yaml
- [ ] `just build agent-crews` produces `.kiro/` at repo root
- [ ] Generated agents are functionally equivalent to (or better than) hand-crafted versions
- [ ] Fresh clone with no fleet.yaml can run `just build agent-crews` successfully
- [ ] Other projects still generate to `projects/{name}/.kiro/` as before
- [ ] `just build && just build && git diff --exit-code .kiro/` passes (idempotent)
