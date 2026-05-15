# agent-crews justfile
# Usage: just <recipe>    List all: just --list
set windows-shell := ["powershell.exe", "-c"]

# ─── Primary Commands (JTBD-aligned) ─────────────────────────────────────────

# Generate all projects (crews + components + steering)
build:
    uv run generate.py --all

# Create/update symlink from fleet.local.yaml path to project .kiro/
link project:
    #!/usr/bin/env bash
    set -e
    TARGET=$(python3 -c "import yaml; d=yaml.safe_load(open('fleet.local.yaml')); print(d['deployments']['{{project}}'])")
    TARGET="${TARGET/#\~/$HOME}"
    if [ -z "$TARGET" ]; then echo "Project {{project}} not in fleet.local.yaml"; exit 1; fi
    # Preserve memory if it exists
    if [ -d "$TARGET/.kiro/memory" ]; then
      cp -r "$TARGET/.kiro/memory" /tmp/.kiro-memory-{{project}}
    fi
    rm -rf "$TARGET/.kiro"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
      cmd //c mklink //d "$(cygpath -w "$TARGET/.kiro")" "$(cygpath -w "$(pwd)/projects/{{project}}/.kiro")"
    else
      ln -sf "$(pwd)/projects/{{project}}/.kiro" "$TARGET/.kiro"
    fi
    # Restore memory
    if [ -d /tmp/.kiro-memory-{{project}} ]; then
      mv /tmp/.kiro-memory-{{project}} "$TARGET/.kiro/memory"
      echo "  ✔ memory preserved"
    fi
    echo "Linked: projects/{{project}}/.kiro → $TARGET/.kiro"

# Show deployment status (what's deployed where)
status:
    #!/usr/bin/env bash
    echo "Fleet Status:"
    python3 scripts/status.py

# Validate all projects (schema + health + components)
check:
    uv run generate.py --check-health

# Setup all projects from fleet.local.yaml (generate + link)
bootstrap:
    #!/usr/bin/env bash
    set -e
    echo "=== Building all ==="
    just build
    echo ""
    echo "=== Linking deployments ==="
    python3 scripts/bootstrap-list.py | while read proj; do
      just link "$proj" 2>/dev/null && echo "  ✅ $proj" || echo "  ❌ $proj (target missing?)"
    done

# ─── Generation ──────────────────────────────────────────────────────────────

# Generate agents for a specific project
generate project:
    uv run generate.py projects/{{project}}/.kiro/crew.yaml

# Generate all (alias for build)
generate-all: build

# Generate component steering + subagents only
components:
    uv run generate.py --components

# Sync shared steering docs to all projects
sync-steering:
    uv run generate.py --sync-steering

# ─── Validation ──────────────────────────────────────────────────────────────

# Validate generated JSON against kiro-cli schema
validate project=".kiro":
    #!/usr/bin/env bash
    set -e
    DIR="{{project}}/agents"
    if [ "{{project}}" != ".kiro" ]; then DIR="projects/{{project}}/.kiro/agents"; fi
    echo "Validating agents in $DIR..."
    FAIL=0
    for f in "$DIR"/*.json; do
      name=$(basename "$f" .json)
      if kiro-cli agent validate --path "$f" 2>&1 | grep -qi "error\|invalid\|malformed"; then
        echo "  ❌ $name"
        FAIL=1
      else
        echo "  ✅ $name"
      fi
    done
    if [ $FAIL -eq 0 ]; then echo "All agents valid"; else exit 1; fi

# Full CI: generate + validate + health check
ci:
    #!/usr/bin/env bash
    set -e
    echo "=== Generate ==="
    just build
    echo ""
    echo "=== Health Check ==="
    just check
    echo ""
    echo "✅ CI pass"

# ─── Deployment ──────────────────────────────────────────────────────────────

# Deploy a crew to a target path (copy, not symlink)
deploy project target:
    rm -rf {{target}}/.kiro
    cp -r projects/{{project}}/.kiro {{target}}/.kiro
    @echo "Deployed projects/{{project}}/.kiro → {{target}}/.kiro"

# Generate + deploy
ship project target: (generate project) (deploy project target)

# ─── Analysis ────────────────────────────────────────────────────────────────

# List recent sessions for a project
sessions project:
    uv run analyze-session.py --project {{project}}

# Analyze a specific session
analyze id *args:
    uv run analyze-session.py {{id}} {{args}}

# Compliance check on most recent session
compliance-last project:
    #!/usr/bin/env bash
    SESSION=$(uv run analyze-session.py --project {{project}} 2>/dev/null | tail -n +3 | head -1 | awk '{print $1}')
    if [ -z "$SESSION" ]; then echo "No sessions found for {{project}}"; exit 1; fi
    echo "Checking session: $SESSION"
    uv run analyze-session.py "$SESSION" --compliance

# Ingest sessions for a project (all tools)
ingest project:
    uv run session-ingest.py --ingest ~/code/{{project}} --since 30d

# Ingest all registered projects
ingest-all:
    #!/usr/bin/env bash
    set -e
    for proj in $(python3 -c "import yaml; d=yaml.safe_load(open('fleet.yaml')); [print(k) for k in d.get('projects',{}).keys() if k != 'agent-crews']"); do
        echo "Ingesting: $proj"
        just ingest "$proj" 2>/dev/null || echo "  ⚠ no sessions for $proj"
    done

# ─── Testing ─────────────────────────────────────────────────────────────────

# Run behavioral smoke tests
smoke-test target:
    ./scripts/smoke-test.sh {{target}}

# Run integration tests
integration-test target:
    ./integration-test.sh {{target}}

# ─── Evaluation ──────────────────────────────────────────────────────────────

# Run model-based crew evaluations (all)
eval:
    uv run scripts/eval-crew.py

# Run routing evals only
eval-routing:
    uv run scripts/eval-crew.py --tag routing

# Run scope evals only
eval-scope:
    uv run scripts/eval-crew.py --tag scope

# Run component evals only
eval-components:
    uv run scripts/eval-crew.py --tag components

# Run evals in verbose mode
eval-verbose:
    uv run scripts/eval-crew.py --verbose

# Dry run (show what would run)
eval-dry:
    uv run scripts/eval-crew.py --dry-run

# ─── Release ─────────────────────────────────────────────────────────────────

# Cut a release: just release <major|minor|patch>
release bump:
    uv run scripts/release.py {{bump}}

# Cut and push: just release-push <major|minor|patch>
release-push bump:
    uv run scripts/release.py {{bump}} --push

# Create platform release (GitHub/GitLab) from latest tag
publish:
    #!/usr/bin/env bash
    set -e
    VERSION=$(cat version.txt)
    TAG="v$VERSION"
    # Extract latest release notes from CHANGELOG.md
    NOTES=$(sed -n "/^## \[$VERSION\]/,/^## \[/p" CHANGELOG.md | sed '1d;$d')
    if command -v gh &>/dev/null; then
        echo "Creating GitHub release $TAG..."
        gh release create "$TAG" --title "$TAG" --notes "$NOTES"
    elif command -v glab &>/dev/null; then
        echo "Creating GitLab release $TAG..."
        glab release create "$TAG" --notes "$NOTES"
    else
        echo "No platform CLI found (gh, glab). Push tag manually."
        echo "Tag $TAG is ready. Push with: git push --tags"
    fi