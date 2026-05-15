#!/usr/bin/env bash
set -euo pipefail

# Mark a change-point after build if generated output differs.
# Called by `just build` post-step. Appends to scratch/change-markers.yaml.
#
# Usage: scripts/mark-change.sh [project-name]
#   If no project given, checks .kiro/agents/ (self-hosted meta crew).

PROJECT="${1:-agent-crews}"
MARKERS_FILE="scratch/change-markers.yaml"

# Determine output dir to check
if [[ "$PROJECT" == "agent-crews" ]]; then
  OUTPUT_DIR=".kiro/agents"
else
  OUTPUT_DIR="projects/$PROJECT/.kiro/agents"
fi

# Check if generated output has uncommitted changes
CHANGED_FILES=$(git diff --name-only "$OUTPUT_DIR" 2>/dev/null || true)
# Also include untracked (new agents)
UNTRACKED=$(git ls-files --others --exclude-standard "$OUTPUT_DIR" 2>/dev/null || true)
CHANGED_FILES=$(printf '%s\n%s' "$CHANGED_FILES" "$UNTRACKED" | grep -v '^$' | sort -u)

if [[ -z "$CHANGED_FILES" ]]; then
  exit 0
fi

# Gather marker data
TIMESTAMP=$(date -Iseconds)
COMMIT=$(git log -1 --format='%h' 2>/dev/null || echo "uncommitted")
DESCRIPTION=$(git log -1 --format='%s' 2>/dev/null || echo "no commit message")
AGENTS_CHANGED=$(echo "$CHANGED_FILES" | xargs -I{} basename {} .json | sort | paste -sd, -)

# Ensure scratch dir exists
mkdir -p "$(dirname "$MARKERS_FILE")"

# Append marker
cat >> "$MARKERS_FILE" << EOF

  - date: "$TIMESTAMP"
    commit: "$COMMIT"
    description: "$DESCRIPTION"
    agents_changed: [$AGENTS_CHANGED]
    project: $PROJECT
EOF

# Initialize file header if first entry
if ! grep -q "^markers:" "$MARKERS_FILE" 2>/dev/null; then
  sed -i '1i markers:' "$MARKERS_FILE"
fi

echo "📍 Change marker recorded: $COMMIT ($AGENTS_CHANGED)"
