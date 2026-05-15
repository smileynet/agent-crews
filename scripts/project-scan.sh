#!/usr/bin/env bash
# One-shot project analysis for crew creation decisions.
# Usage: ./scripts/project-scan.sh <project-path>
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/project-scan.sh <project-path>

One-shot project analysis: stack, build tools, structure, existing agents, session history.
Output is structured for direct use by crew-creator.

Examples:
  ./scripts/project-scan.sh ~/code/my-project
  ./scripts/project-scan.sh .
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && show_help

TARGET="${1:?Usage: project-scan.sh <project-path>}"
TARGET="${TARGET/#\~/$HOME}"
TARGET=$(cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET")

if [ ! -d "$TARGET" ]; then
  echo "Error: $TARGET is not a directory" >&2
  exit 2
fi

NAME=$(basename "$TARGET")
SCRIPT_DIR=$(cd "$(dirname "$0")/.." && pwd)

echo "=== PROJECT SCAN: $NAME ==="
echo ""

# --- Stack Detection ---
echo "stack:"

# Language
LANG="unknown"
FRAMEWORK="none"
if [ -f "$TARGET/package.json" ]; then
  LANG="typescript"
  # Check if actually JS (no tsconfig)
  [ ! -f "$TARGET/tsconfig.json" ] && LANG="javascript"
  # Framework detection
  if grep -q '"next"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="next";
  elif grep -q '"react"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="react";
  elif grep -q '"express"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="express";
  elif grep -q '"fastify"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="fastify";
  elif grep -q '"svelte"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="svelte";
  elif grep -q '"vue"' "$TARGET/package.json" 2>/dev/null; then FRAMEWORK="vue";
  fi
elif [ -f "$TARGET/Cargo.toml" ]; then
  LANG="rust"
  if grep -q 'bevy' "$TARGET/Cargo.toml" 2>/dev/null; then FRAMEWORK="bevy";
  elif grep -q 'actix' "$TARGET/Cargo.toml" 2>/dev/null; then FRAMEWORK="actix";
  elif grep -q 'axum' "$TARGET/Cargo.toml" 2>/dev/null; then FRAMEWORK="axum";
  elif grep -q 'tokio' "$TARGET/Cargo.toml" 2>/dev/null; then FRAMEWORK="tokio";
  fi
elif [ -f "$TARGET/pyproject.toml" ] || [ -f "$TARGET/setup.py" ]; then
  LANG="python"
  if grep -q 'django' "$TARGET/pyproject.toml" 2>/dev/null; then FRAMEWORK="django";
  elif grep -q 'fastapi' "$TARGET/pyproject.toml" 2>/dev/null; then FRAMEWORK="fastapi";
  elif grep -q 'flask' "$TARGET/pyproject.toml" 2>/dev/null; then FRAMEWORK="flask";
  fi
elif [ -f "$TARGET/go.mod" ]; then
  LANG="go"
elif [ -f "$TARGET/project.godot" ]; then
  LANG="gdscript"
  FRAMEWORK="godot"
elif [ -f "$TARGET/pom.xml" ] || [ -f "$TARGET/build.gradle" ]; then
  LANG="java"
fi
echo "  language: $LANG"
echo "  framework: $FRAMEWORK"

# Build tools
BUILD=""; TEST=""; LINT=""
TASK_RUNNER="none"
PKG_MGR="none"

if [ -f "$TARGET/.mise.toml" ]; then
  TASK_RUNNER="mise"
  BUILD=$(grep -A1 '\[tasks.build\]' "$TARGET/.mise.toml" 2>/dev/null | grep 'run' | sed 's/.*= *"\(.*\)"/\1/' | head -1 || true)
  TEST=$(grep -A1 '\[tasks.test\]' "$TARGET/.mise.toml" 2>/dev/null | grep 'run' | sed 's/.*= *"\(.*\)"/\1/' | head -1 || true)
  LINT=$(grep -A1 '\[tasks.lint\]' "$TARGET/.mise.toml" 2>/dev/null | grep 'run' | sed 's/.*= *"\(.*\)"/\1/' | head -1 || true)
  [ -n "$BUILD" ] || BUILD="mise run build"
  [ -n "$TEST" ] || TEST="mise run test"
elif [ -f "$TARGET/justfile" ]; then
  TASK_RUNNER="just"
  grep -q '^build' "$TARGET/justfile" 2>/dev/null && BUILD="just build" || true
  grep -q '^test' "$TARGET/justfile" 2>/dev/null && TEST="just test" || true
  grep -q '^lint' "$TARGET/justfile" 2>/dev/null && LINT="just lint" || true
elif [ -f "$TARGET/Makefile" ]; then
  TASK_RUNNER="make"
  grep -q '^build' "$TARGET/Makefile" 2>/dev/null && BUILD="make build" || true
  grep -q '^test' "$TARGET/Makefile" 2>/dev/null && TEST="make test" || true
  grep -q '^lint' "$TARGET/Makefile" 2>/dev/null && LINT="make lint" || true
fi

if [ "$LANG" = "typescript" ] || [ "$LANG" = "javascript" ]; then
  if [ -f "$TARGET/pnpm-lock.yaml" ]; then PKG_MGR="pnpm";
  elif [ -f "$TARGET/yarn.lock" ]; then PKG_MGR="yarn";
  elif [ -f "$TARGET/bun.lockb" ]; then PKG_MGR="bun";
  else PKG_MGR="npm"; fi
  # Fallback to package.json scripts
  [ -z "$BUILD" ] && grep -q '"build"' "$TARGET/package.json" 2>/dev/null && BUILD="$PKG_MGR run build" || true
  [ -z "$TEST" ] && grep -q '"test"' "$TARGET/package.json" 2>/dev/null && TEST="$PKG_MGR run test" || true
  [ -z "$LINT" ] && grep -q '"lint"' "$TARGET/package.json" 2>/dev/null && LINT="$PKG_MGR run lint" || true
elif [ "$LANG" = "rust" ]; then
  PKG_MGR="cargo"
  [ -z "$BUILD" ] && BUILD="cargo build"
  [ -z "$TEST" ] && TEST="cargo test"
  [ -z "$LINT" ] && LINT="cargo clippy"
elif [ "$LANG" = "python" ]; then
  if [ -f "$TARGET/uv.lock" ]; then PKG_MGR="uv";
  elif [ -f "$TARGET/poetry.lock" ]; then PKG_MGR="poetry";
  else PKG_MGR="pip"; fi
  [ -z "$TEST" ] && TEST="pytest"
  [ -z "$LINT" ] && LINT="ruff check"
elif [ "$LANG" = "go" ]; then
  PKG_MGR="go"
  [ -z "$BUILD" ] && BUILD="go build ./..."
  [ -z "$TEST" ] && TEST="go test ./..."
  [ -z "$LINT" ] && LINT="golangci-lint run"
fi

# Detect specific test/lint tools from config files
{ [ -f "$TARGET/vitest.config.ts" ] || [ -f "$TARGET/vitest.config.js" ]; } && TEST="vitest" || true
{ [ -f "$TARGET/jest.config.ts" ] || [ -f "$TARGET/jest.config.js" ]; } && TEST="jest" || true
{ [ -f "$TARGET/biome.json" ] || [ -f "$TARGET/biome.jsonc" ]; } && LINT="biome check" || true
{ [ -f "$TARGET/.eslintrc.json" ] || [ -f "$TARGET/eslint.config.js" ]; } && LINT="eslint ." || true

echo "  build: ${BUILD:-null}"
echo "  test: ${TEST:-null}"
echo "  lint: ${LINT:-null}"
echo "  package_manager: $PKG_MGR"
echo "  task_runner: $TASK_RUNNER"

# --- Structure ---
echo ""
echo "structure:"
FILE_COUNT=$(find "$TARGET" -type f \
  -not -path '*/.git/*' -not -path '*/node_modules/*' \
  -not -path '*/target/*' -not -path '*/dist/*' \
  -not -path '*/build/*' -not -path '*/__pycache__/*' \
  -not -path '*/.cache/*' 2>/dev/null | wc -l)
echo "  total_files: $FILE_COUNT"

# Source dirs
SRC_DIRS=$(find "$TARGET" -maxdepth 2 -type d \( -name 'src' -o -name 'lib' -o -name 'packages' -o -name 'crates' -o -name 'cmd' -o -name 'internal' \) 2>/dev/null | sed "s|$TARGET/||" | paste -sd, | sed 's/,$//')
echo "  src_dirs: [${SRC_DIRS:-none}]"

# Test dirs
TEST_DIRS=$(find "$TARGET" -maxdepth 2 -type d \( -name 'tests' -o -name 'test' -o -name '__tests__' -o -name 'spec' \) 2>/dev/null | sed "s|$TARGET/||" | paste -sd, | sed 's/,$//')
echo "  test_dirs: [${TEST_DIRS:-none}]"

# Config files
CONFIGS=$(find "$TARGET" -maxdepth 1 -type f \( \
  -name 'package.json' -o -name 'tsconfig.json' -o -name 'Cargo.toml' -o -name 'pyproject.toml' \
  -o -name '.mise.toml' -o -name 'justfile' -o -name 'Makefile' -o -name 'docker-compose.yml' \
  -o -name 'Dockerfile' -o -name 'terraform.tf' -o -name '*.tf' -o -name 'cdk.json' \
  -o -name 'biome.json' -o -name 'biome.jsonc' -o -name '.eslintrc*' -o -name 'vitest.config.*' \
  \) 2>/dev/null | sed "s|$TARGET/||" | sort | paste -sd, | sed 's/,$//')
echo "  config_files: [${CONFIGS:-none}]"

# --- Existing Agents ---
echo ""
echo "existing_agents:"
if [ -d "$TARGET/.kiro/agents" ]; then
  AGENT_COUNT=$(ls "$TARGET/.kiro/agents/"*.json 2>/dev/null | wc -l)
  AGENTS=$(ls "$TARGET/.kiro/agents/"*.json 2>/dev/null | xargs -I{} basename {} .json | paste -sd, | sed 's/,$//')
  echo "  has_kiro: true"
  echo "  count: $AGENT_COUNT"
  echo "  agents: [$AGENTS]"
  # Detect crews from crew files
  if [ -d "$TARGET/.crews" ]; then
    CREWS=$(ls "$TARGET/.crews/"*.yaml 2>/dev/null | xargs -I{} basename {} .yaml | paste -sd, | sed 's/,$//')
    echo "  crews: [$CREWS]"
  fi
else
  echo "  has_kiro: false"
fi

# --- Session History ---
echo ""
echo "session_history:"
if command -v uv &>/dev/null && [ -f "$SCRIPT_DIR/session-ingest.py" ]; then
  SUMMARY=$(cd "$SCRIPT_DIR" && uv run session-ingest.py --project "$TARGET" --since 30d --output summary 2>/dev/null)
  if [ -n "$SUMMARY" ]; then
    # Extract key metrics from summary output
    SESSIONS=$(echo "$SUMMARY" | grep -c ':' 2>/dev/null || echo "0")
    # Use python to parse the structured output
    cd "$SCRIPT_DIR" && python3 -c "
import json, subprocess, sys
from pathlib import Path
try:
    # Run ingest to get summary.json
    name = Path('$TARGET').name
    summary_file = Path('scratch/sessions') / name / 'summary.json'
    if not summary_file.exists():
        subprocess.run(['uv', 'run', 'session-ingest.py', '--ingest', '$TARGET', '--since', '30d'],
                       capture_output=True, timeout=30)
    if summary_file.exists():
        d = json.loads(summary_file.read_text())
        tools = ', '.join(f'{k}: {v}' for k,v in d.get('sessions_by_tool',{}).items())
        total_sessions = sum(d.get('sessions_by_tool',{}).values())
        intents = d.get('intent_distribution',{})
        top_intent = max(intents, key=intents.get) if intents else 'unknown'
        print(f'  tools_used: [{tools}]')
        print(f'  sessions_30d: {total_sessions}')
        print(f'  primary_intent: {top_intent}')
        print(f'  tokens_30d: {d.get("tokens_total", 0):,}')
        print(f'  cost_30d (derived): \${d.get("cost_total", 0):.2f}')
    else:
        print('  sessions_30d: 0')
        print('  note: no sessions found')
except Exception:
    print('  sessions_30d: 0')
    print('  note: session-ingest unavailable')
" 2>/dev/null || echo "  sessions_30d: 0"
  fi
else
  echo "  sessions_30d: 0"
  echo "  note: session-ingest not available"
fi

# --- Recommendation ---
echo ""
echo "recommendation:"

# Build recommendation based on signals
CREWS="general"
REASON="General crew is always included."

# Check for infra signals
HAS_INFRA=false
if [ -f "$TARGET/terraform.tf" ] || [ -f "$TARGET/cdk.json" ] || [ -f "$TARGET/docker-compose.yml" ]; then
  HAS_INFRA=true
elif find "$TARGET" -maxdepth 2 -name '*.tf' -type f 2>/dev/null | grep -q .; then
  HAS_INFRA=true
fi
if [ "$HAS_INFRA" = "true" ]; then
  CREWS="$CREWS, infrastructure"
  REASON="$REASON Infrastructure files detected."
fi

# Check for heavy test presence
TEST_FILE_COUNT=$(find "$TARGET" -type f \( -name '*test*' -o -name '*spec*' \) -not -path '*node_modules*' -not -path '*/.git/*' 2>/dev/null | wc -l)
if [ "$TEST_FILE_COUNT" -gt 10 ]; then
  CREWS="$CREWS, bug-fix"
  REASON="$REASON Heavy test suite ($TEST_FILE_COUNT test files)."
fi

# Check for docs
DOC_COUNT=$(find "$TARGET" -maxdepth 2 -type f \( -name '*.md' -o -name '*.rst' \) -not -path '*node_modules*' -not -path '*/.git/*' 2>/dev/null | wc -l)
if [ "$DOC_COUNT" -gt 10 ]; then
  CREWS="$CREWS, research"
  REASON="$REASON Significant documentation ($DOC_COUNT doc files)."
fi

echo "  crews: [$CREWS]"
echo "  reason: \"$REASON\""
