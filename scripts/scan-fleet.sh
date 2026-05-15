#!/usr/bin/env bash
# Scan a directory for projects with .crews/ and update fleet.local.yaml
# Usage: ./scripts/scan-fleet.sh [search-dir]
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/scan-fleet.sh [search-dir]

Discover projects with .crews/crew.yaml and update fleet.local.yaml.
Default search directory: ~/code

Examples:
  ./scripts/scan-fleet.sh              # scan ~/code
  ./scripts/scan-fleet.sh ~/projects   # scan custom dir
  ./scripts/scan-fleet.sh --dry-run    # show what would be added
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && show_help

DRY_RUN=false
SEARCH_DIR="$HOME/code"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    *) SEARCH_DIR="${arg/#\~/$HOME}" ;;
  esac
done

if [ ! -d "$SEARCH_DIR" ]; then
  echo "Error: $SEARCH_DIR is not a directory" >&2
  exit 2
fi

SCRIPT_DIR=$(cd "$(dirname "$0")/.." && pwd)
FLEET_FILE="$SCRIPT_DIR/fleet.local.yaml"

echo "Scanning: $SEARCH_DIR"
echo ""

# Find all .crews/crew.yaml files
FOUND=0
ENTRIES=""
while IFS= read -r crew_file; do
  proj_dir=$(dirname $(dirname "$crew_file"))
  name=$(basename "$proj_dir")
  # Use ~ shorthand for home paths
  display_path="${proj_dir/#$HOME/\~}"
  echo "  found: $name -> $display_path"
  ENTRIES="$ENTRIES  $name: $display_path\n"
  FOUND=$((FOUND + 1))
done < <(find "$SEARCH_DIR" -maxdepth 3 -path '*/.crews/crew.yaml' -type f 2>/dev/null | sort)

echo ""
echo "Found: $FOUND projects"

if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "Would write to $FLEET_FILE:"
  echo "---"
  printf "projects:\n$ENTRIES"
  exit 0
fi

if [ $FOUND -eq 0 ]; then
  echo "No projects found."
  exit 0
fi

# Write fleet.local.yaml
printf "# fleet.local.yaml \u2014 project registry (auto-maintained by scanner)\nprojects:\n$ENTRIES" > "$FLEET_FILE"
echo "Updated: $FLEET_FILE"
