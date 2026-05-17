# agent-crews justfile
# Usage: just <recipe>    List all: just --list
set windows-shell := ["powershell.exe", "-c"]

# ─── Build ─────────────────────────────────────────────────────────────────────

# Generate all projects (reads fleet.local.yaml, writes .kiro/ in each project)
build *args:
    uv run generate.py {{args}}
    @./scripts/mark-change.sh 2>/dev/null || true

# Generate all projects (explicit)
build-all:
    uv run generate.py --all

# Push staging to project (first-gen workflow: copies .crews/ + .kiro/, deletes staging)
push project:
    #!/usr/bin/env bash
    set -e
    STAGING="projects/{{project}}"
    if [ ! -d "$STAGING" ]; then echo "No staging for {{project}}"; exit 1; fi
    TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['projects']['{{project}}'])")
    TARGET="${TARGET/#\~/$HOME}"
    if [ -z "$TARGET" ]; then echo "{{project}} not in fleet.local.yaml"; exit 1; fi
    echo "Pushing: $STAGING -> $TARGET"
    # Copy .crews/ (source)
    if [ -d "$STAGING/.crews" ]; then
      mkdir -p "$TARGET/.crews"
      cp -r "$STAGING/.crews/"* "$TARGET/.crews/"
      echo "  ✓ .crews/"
    fi
    # Copy .kiro/ (generated output)
    if [ -d "$STAGING/.kiro" ]; then
      rm -rf "$TARGET/.kiro"
      cp -r "$STAGING/.kiro" "$TARGET/.kiro"
      echo "  ✓ .kiro/"
    fi
    # Delete staging
    rm -rf "$STAGING"
    echo "  ✓ staging deleted"
    echo "Done: {{project}} deployed to $TARGET"

# Scan for projects with .crews/ and update fleet.local.yaml
scan *args:
    ./scripts/scan-fleet.sh {{args}}

# ─── Deploy (dev iteration) ───────────────────────────────────────────────────

# Symlink for rapid dev iteration (opt-in, not default)
link project:
    #!/usr/bin/env bash
    set -e
    TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['projects']['{{project}}'])")
    TARGET="${TARGET/#\~/$HOME}"
    if [ -z "$TARGET" ]; then echo "{{project}} not in fleet.local.yaml"; exit 1; fi
    STAGING="projects/{{project}}"
    if [ ! -d "$STAGING/.kiro" ]; then echo "No staging .kiro/ for {{project}}. Run: just build --staging {{project}}"; exit 1; fi
    rm -rf "$TARGET/.kiro"
    ln -sf "$(pwd)/$STAGING/.kiro" "$TARGET/.kiro"
    echo "Linked: $STAGING/.kiro -> $TARGET/.kiro (dev mode)"

# ─── Validation ──────────────────────────────────────────────────────────

# Check crew health for a project
check project:
    ./scripts/crew-health.sh {{project}}

# Show fleet status
status:
    #!/usr/bin/env bash
    echo "Fleet (fleet.local.yaml):"
    python3 << 'EOF'
    import yaml
    from pathlib import Path
    d = yaml.safe_load(open('fleet.local.yaml'))
    for name, path in d.get('projects', {}).items():
        p = Path(path).expanduser()
        has_crews = '✅' if (p / '.crews' / 'crew.yaml').exists() else '❌'
        has_kiro = '✅' if (p / '.kiro' / 'agents').exists() else '❌'
        print(f'  {has_crews} {has_kiro} {name:<20} {path}')
    print()
    print('Legend: [.crews/] [.kiro/] name  path')
    EOF

# ─── Evaluation ──────────────────────────────────────────────────────────

# Run evals for a project (finds .crews/evals.yaml)
eval *project:
    #!/usr/bin/env bash
    set -e
    if [ -z "{{project}}" ]; then
      # No arg: run this repo's own evals
      if [ -f ".crews/evals.yaml" ]; then
        uv run scripts/eval-crew.py --fixture .crews/evals.yaml --parallel 5
      else
        uv run scripts/eval-crew.py --parallel 5
      fi
    else
      TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['projects']['{{project}}'])")
      TARGET="${TARGET/#\~/$HOME}"
      FIXTURE="$TARGET/.crews/evals.yaml"
      if [ ! -f "$FIXTURE" ]; then echo "No evals: $FIXTURE"; exit 1; fi
      uv run scripts/eval-crew.py --fixture "$FIXTURE" --parallel 5
    fi

# Run evals in verbose mode
eval-verbose *project:
    #!/usr/bin/env bash
    set -e
    if [ -z "{{project}}" ]; then
      uv run scripts/eval-crew.py --verbose
    else
      TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['projects']['{{project}}'])")
      TARGET="${TARGET/#\~/$HOME}"
      uv run scripts/eval-crew.py --fixture "$TARGET/.crews/evals.yaml" --verbose
    fi

# Dry run evals
eval-dry *project:
    #!/usr/bin/env bash
    set -e
    if [ -z "{{project}}" ]; then
      uv run scripts/eval-crew.py --dry-run
    else
      TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['projects']['{{project}}'])")
      TARGET="${TARGET/#\~/$HOME}"
      uv run scripts/eval-crew.py --fixture "$TARGET/.crews/evals.yaml" --dry-run
    fi

# ─── Analysis ───────────────────────────────────────────────────────────

# Session summary for a project
summary project:
    ./scripts/session-summary.sh ~/code/{{project}}

# Cross-tool comparison
compare project:
    uv run analyze-session.py --compare ~/code/{{project}}

# Session diff (before/after)
diff project date:
    ./scripts/session-diff.sh ~/code/{{project}} {{date}}

# Ingest sessions for a project
ingest project:
    uv run session-ingest.py --ingest ~/code/{{project}} --since 30d

# Ingest all projects
ingest-all:
    #!/usr/bin/env bash
    set -e
    python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); [print(k) for k in d.get('projects',{}).keys()]" | while read proj; do
        echo "Ingesting: $proj"
        just ingest "$proj" 2>/dev/null || echo "  ⚠ no sessions for $proj"
    done

# ─── Testing ────────────────────────────────────────────────────────────

# Run unit + e2e tests
test:
    uv run --with pytest --with pyyaml pytest tests/ -v

# Run behavioral smoke tests
smoke-test target:
    ./scripts/smoke-test.sh {{target}}

# ─── Migration ──────────────────────────────────────────────────────────

# Migrate a project from old .kiro/-mixed to .crews/ layout
migrate project:
    ./scripts/migrate-to-crews.sh ~/code/{{project}}
