#!/usr/bin/env bash
# Migrate a project from .kiro/-mixed to .crews/ (source) + .kiro/ (output)
# Usage: ./scripts/migrate-to-crews.sh <project-path>
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/migrate-to-crews.sh <project-path>

Migrate a project from the old layout (.kiro/ contains everything) to the new
layout (.crews/ for source, .kiro/ for kiro-native output only).

Examples:
  ./scripts/migrate-to-crews.sh ~/code/pidev-crafter
  ./scripts/migrate-to-crews.sh ~/code/craft-mmo
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && show_help

TARGET="${1:?Usage: migrate-to-crews.sh <project-path>}"
TARGET="${TARGET/#\~/$HOME}"
TARGET=$(cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET")

if [ ! -d "$TARGET" ]; then
  echo "Error: $TARGET is not a directory" >&2
  exit 2
fi

NAME=$(basename "$TARGET")
echo "=== Migrating: $NAME ==="

# Create .crews/
mkdir -p "$TARGET/.crews"

# Move crew.yaml
if [ -f "$TARGET/.kiro/crew.yaml" ]; then
  mv "$TARGET/.kiro/crew.yaml" "$TARGET/.crews/crew.yaml"
  echo "  ✓ crew.yaml"
fi

# Move scripts/
if [ -d "$TARGET/.kiro/scripts" ]; then
  mv "$TARGET/.kiro/scripts" "$TARGET/.crews/scripts"
  echo "  ✓ scripts/"
fi

# Move metadata
if [ -f "$TARGET/.kiro/.agent-crews-meta.json" ]; then
  mv "$TARGET/.kiro/.agent-crews-meta.json" "$TARGET/.crews/meta.json"
  echo "  ✓ meta.json"
fi

# Remove crews/ from .kiro (these are base copies, not needed in .crews/)
if [ -d "$TARGET/.kiro/crews" ]; then
  rm -rf "$TARGET/.kiro/crews"
  echo "  ✓ removed .kiro/crews/ (base copies)"
fi

# Copy evals if they exist in agent-crews tests/
SCRIPT_DIR=$(cd "$(dirname "$0")/.." && pwd)
EVALS="$SCRIPT_DIR/tests/${NAME}-evals.yaml"
if [ -f "$EVALS" ]; then
  cp "$EVALS" "$TARGET/.crews/evals.yaml"
  echo "  ✓ evals.yaml (from tests/)"
fi

echo ""
echo "Result:"
ls "$TARGET/.crews/"
echo ""
echo "Done. .crews/ is now the source of truth for $NAME."
