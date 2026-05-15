#!/bin/bash
# validate.sh — CI validation for agent-crews repo hygiene
set -e

echo "=== agent-crews validation ==="

# Data separation (fleet.yaml is legacy — must stay gitignored)
git check-ignore fleet.yaml || { echo "FAIL: fleet.yaml not gitignored"; exit 1; }
git check-ignore projects/placeholder || { echo "FAIL: projects/ not gitignored"; exit 1; }

# No personal data in committed files
NAMES='lacrosse-bosse|pidot-dev|rustacean-academy|news-scraper|aws-litellm|cgd-review|ue-analysis|games-sa-buddy|craft-mmo|genai-field-lab'
if git ls-files | xargs grep -lE "$NAMES" 2>/dev/null | grep -v 'docs/specs/\|base/crews/meta.yaml\|.kiro/crews/meta.yaml\|.kiro/agents/project-hygiene\|scripts/validate.sh'; then
  echo "FAIL: Personal project names found in committed files"
  exit 1
fi

# fleet.example.yaml valid
python3 -c "import yaml; yaml.safe_load(open('fleet.example.yaml'))" || { echo "FAIL: fleet.example.yaml invalid"; exit 1; }

# Meta crew exists with all agents
for agent in dispatcher crew-creator crew-augmenter crew-doctor crew-analyst crew-researcher kiro-helper project-hygiene; do
  grep -q "name: $agent" base/crews/meta.yaml || { echo "FAIL: $agent missing from meta.yaml"; exit 1; }
done

# Generated agents match meta crew
for agent in dispatcher crew-creator crew-augmenter crew-doctor crew-analyst crew-researcher kiro-helper project-hygiene; do
  test -f .kiro/agents/$agent.json || { echo "FAIL: $agent.json not generated"; exit 1; }
done

# Idempotency
uv run generate.py --all 2>/dev/null
uv run generate.py --all 2>/dev/null
git diff --exit-code .kiro/agents/ .kiro/prompts/ || { echo "FAIL: Generation not idempotent"; exit 1; }

# No stale path references in AGENTS.md
if grep -q 'sa-crew' AGENTS.md; then
  echo "FAIL: AGENTS.md has stale path references"
  exit 1
fi

# CONTRIBUTING.md exists
test -f CONTRIBUTING.md || { echo "FAIL: CONTRIBUTING.md missing"; exit 1; }

echo "=== ALL CHECKS PASSED ==="
