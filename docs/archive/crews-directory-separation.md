# Spec: .crews/ Directory Separation

**Status:** Implemented  
**Date:** 2026-05-15  
**ADR:** [ADR-007](../decisions/ADR-007-crews-directory-separation.md)

## Objective

Separate agent-crews machinery from kiro-native configuration. After this change:
- `.kiro/` contains only files consumed by kiro-cli (generated output)
- `.crews/` contains agent-crews source files (committable, portable, rehydratable)

## Target Layout

### In each project:
```
~/code/my-project/
  .crews/                    ← source (committed)
    crew.yaml                ← full project config
    evals.yaml               ← behavioral smoke tests
    scripts/                 ← notification/validation scripts
    overrides/               ← (optional) project-specific agent overrides
  .kiro/                     ← generated output (optionally committed)
    agents/*.json
    prompts/*.md
    steering/**/*.md
    skills/
```

### In agent-crews repo:
```
agent-crews/
  .crews/                    ← this repo's own crew config
    crew.yaml
    evals.yaml
  .kiro/                     ← this repo's generated agents
  base/crews/                ← base crew templates (general.yaml, bug-fix.yaml, etc.)
  shared/                    ← shared components, steering, skills, themes
  projects/                  ← staging only (gitignored, temporary)
  fleet.local.yaml           ← project registry (gitignored)
  bin/agent-crews            ← CLI wrapper
```

## .crews/crew.yaml Format

Fully self-contained. No inheritance. All config inlined:

```yaml
# .crews/crew.yaml — pidev-crafter
persona: personal
crews: [general, bug-fix, research]
theme: null
components:
  sanity_gate: assumption-register
  search:
    variant: layered
    sources: [local, web]
  memory:
    variant: four-tier
    tiers: [working, session]
  notifications:
    variant: channels
    channels: [toast]
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
  verification:
    variant: gate
    checks:
      build: "mise run build"
      test: "mise run test"
      lint: null
  git:
    variant: checkpoint
  completion:
    variant: standard
    followups: file-issues
```

## fleet.local.yaml Format

```yaml
# fleet.local.yaml — project registry (auto-maintained by scanner)
projects:
  agent-crews: ~/code/agent-crews
  pidev-crafter: ~/code/pidev-crafter
  craft-mmo: ~/code/craft-mmo
  lacrosse-bosse: ~/code/lacrosse-bosse
```

Name is directory basename. Path is absolute or ~-relative.

## Workflows

### Normal: edit and rebuild
```bash
# Edit crew config in-project
vim ~/code/foo/.crews/crew.yaml

# Rebuild (from agent-crews or from project with wrapper)
just build foo
# OR: agent-crews build (from project cwd)
```

### First-gen: new project
```bash
# From agent-crews
just build --staging foo     # crew-creator writes to projects/foo/.crews/
# Inspect staging output
ls projects/foo/.kiro/agents/
# Push to project
just push foo                # copies .crews/ + .kiro/ to ~/code/foo/, deletes staging
```

### Scan and discover
```bash
# Find all projects with .crews/ under ~/code
just scan ~/code
# Updates fleet.local.yaml automatically
```

### Run evals
```bash
# From project directory
cd ~/code/foo && agent-crews eval
# Finds .crews/evals.yaml automatically

# From agent-crews, by name
just eval foo
```

## Commands (justfile)

| Command | Action |
|---------|--------|
| `just build` | Rebuild all projects in fleet.local.yaml |
| `just build foo` | Rebuild one project by name |
| `just build .` | Rebuild project in cwd |
| `just build --staging foo` | First-gen into projects/foo/ (crew-creator writes here directly) |
| `just push foo` | Copy staging to target, delete staging |
| `just link foo` | Symlink for dev iteration (opt-in) |
| `just scan <dir>` | Discover .crews/ dirs, update fleet.local.yaml |
| `just eval` | Run evals for cwd project |
| `just eval foo` | Run evals for named project |
| `just status` | Show fleet.local.yaml projects and health |

## bin/agent-crews Wrapper

```bash
#!/usr/bin/env bash
# Resolves AGENT_CREWS_HOME and delegates to generate.py
set -euo pipefail
HOME_DIR="${AGENT_CREWS_HOME:?Set AGENT_CREWS_HOME to your agent-crews repo path}"
exec uv run "$HOME_DIR/generate.py" "$@"
```

Install: add `$AGENT_CREWS_HOME/bin` to PATH (via mise or shell profile).

## Scanner Script

```bash
# scripts/scan-fleet.sh <search-dir>
# Finds all directories containing .crews/crew.yaml
# Outputs fleet.local.yaml format
find <dir> -maxdepth 3 -name 'crew.yaml' -path '*/.crews/*' \
  | while read f; do
    proj=$(dirname $(dirname "$f"))
    name=$(basename "$proj")
    echo "  $name: $proj"
  done
```

## generate.py Changes

### Input resolution
```python
def resolve_project(name_or_path: str) -> Path:
    """Resolve project name or '.' to .crews/crew.yaml path."""
    if name_or_path == '.':
        # Walk up from cwd looking for .crews/crew.yaml
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / '.crews' / 'crew.yaml').exists():
                return cwd / '.crews' / 'crew.yaml'
            cwd = cwd.parent
        sys.exit('No .crews/crew.yaml found in cwd or parents')
    # Look up in fleet.local.yaml
    fleet = load_fleet_local()
    path = fleet['projects'].get(name_or_path)
    if path:
        return Path(path).expanduser() / '.crews' / 'crew.yaml'
    sys.exit(f'Project not found: {name_or_path}')
```

### Output location
```python
def output_dir(crew_yaml: Path) -> Path:
    """Output .kiro/ next to .crews/ (sibling directory)."""
    return crew_yaml.parent.parent / '.kiro'
```

### Staging mode
```python
def staging_dir(name: str) -> Path:
    """Staging output in agent-crews/projects/<name>/"""
    return AGENT_CREWS_ROOT / 'projects' / name
```

## Eval Runner Changes

```python
def find_fixture() -> Path:
    """Find evals.yaml: explicit arg > .crews/evals.yaml in cwd."""
    cwd = Path.cwd()
    while cwd != cwd.parent:
        candidate = cwd / '.crews' / 'evals.yaml'
        if candidate.exists():
            return candidate
        cwd = cwd.parent
    sys.exit('No .crews/evals.yaml found. Use --fixture to specify.')
```

## Migration Script

```bash
#!/usr/bin/env bash
# scripts/migrate-to-crews.sh <project-path>
set -euo pipefail
TARGET="${1:?Usage: migrate-to-crews.sh <project-path>}"
TARGET="${TARGET/#\~/$HOME}"

mkdir -p "$TARGET/.crews"

# Move agent-crews files from .kiro/ to .crews/
[ -f "$TARGET/.kiro/crew.yaml" ] && mv "$TARGET/.kiro/crew.yaml" "$TARGET/.crews/crew.yaml"
[ -d "$TARGET/.kiro/crews" ] && rm -rf "$TARGET/.kiro/crews"  # base copies, not needed
[ -f "$TARGET/.kiro/.agent-crews-meta.json" ] && mv "$TARGET/.kiro/.agent-crews-meta.json" "$TARGET/.crews/meta.json"
[ -d "$TARGET/.kiro/scripts" ] && mv "$TARGET/.kiro/scripts" "$TARGET/.crews/scripts"

# Copy evals if they exist in agent-crews tests/
NAME=$(basename "$TARGET")
EVALS="$(dirname "$0")/../tests/${NAME}-evals.yaml"
[ -f "$EVALS" ] && cp "$EVALS" "$TARGET/.crews/evals.yaml"

echo "Migrated: $TARGET/.crews/"
ls "$TARGET/.crews/"
```

## What Gets Deleted

- `fleet.yaml` — replaced by per-project `.crews/crew.yaml`
- `fleet.example.yaml` — replaced by documentation
- `projects/` directory contents — migrated to target projects, then staging-only
- `tests/*-evals.yaml` — moved to respective `.crews/evals.yaml`
- `self_hosted` flag concept — agent-crews is just another project

## Open Items (implementation details, not design)

- Exact `generate.py` refactor plan (phased or big-bang)
- How `base/defaults.yaml` is used by crew-creator when scaffolding new crew.yaml
- Whether `overrides/` uses patch semantics or full replacement
- How the wrapper handles uv availability on PATH

## Success Criteria

- [ ] `.kiro/` contains only kiro-native files
- [ ] `.crews/` contains all agent-crews source files
- [ ] `just build foo` reads from `~/code/foo/.crews/`, writes `~/code/foo/.kiro/`
- [ ] `just build .` works from any project with `.crews/`
- [ ] Eval runner finds `.crews/evals.yaml` in cwd
- [ ] Scanner discovers projects and updates fleet.local.yaml
- [ ] Migration script handles all existing projects
- [ ] agent-crews itself uses `.crews/` (no special case)
- [ ] No regression in generation output
