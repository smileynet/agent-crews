#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/session-summary.sh <project-path> [--since 30d]

Pre-digested session insights across all AI tools (oh-my-pi, codex, kiro-cli, claude-code, opencode).
Shows: tokens/session, intent distribution, failure rate, crew recommendations.

Examples:
  ./scripts/session-summary.sh ~/code/my-project
  ./scripts/session-summary.sh ~/code/my-project --since 7d
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]] && show_help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

PROJECT_PATH="$1"
shift
SINCE="30d"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    *) usage ;;
  esac
done

PROJECT_NAME="$(basename "$(realpath "$PROJECT_PATH")")"

# Ingest sessions → scratch/sessions/<project>/summary.json
uv run "$REPO_DIR/session-ingest.py" --ingest "$PROJECT_PATH" --project "$PROJECT_PATH" --since "$SINCE" >/dev/null 2>&1

SUMMARY_JSON="$REPO_DIR/scratch/sessions/$PROJECT_NAME/summary.json"

if [[ ! -f "$SUMMARY_JSON" ]]; then
  echo "Error: No summary generated at $SUMMARY_JSON" >&2
  exit 1
fi

export SUMMARY_JSON SINCE PROJECT_NAME

# Format summary.json into structured output
python3 << 'PYEOF'
import json, sys, os

summary_json = os.environ['SUMMARY_JSON']
since_label = os.environ['SINCE']
project = os.environ['PROJECT_NAME']

with open(summary_json) as f:
    s = json.load(f)

# Convert since to human label
if since_label.endswith('d'):
    since_human = f'last {since_label[:-1]} days'
elif since_label.endswith('h'):
    since_human = f'last {since_label[:-1]} hours'
else:
    since_human = f'last {since_label}'

sessions_by_tool = s['sessions_by_tool']
total_sessions = sum(sessions_by_tool.values())
sessions_detail = ', '.join(f'{k}: {v}' for k, v in sessions_by_tool.items())

# Format tokens
tokens = s['tokens_total']
if tokens >= 1_000_000:
    tokens_fmt = f'{tokens / 1_000_000:.1f}M'
elif tokens >= 1_000:
    tokens_fmt = f'{tokens / 1_000:.1f}K'
else:
    tokens_fmt = str(tokens)

# Format duration
dur_s = s['avg_session_duration_seconds']
if dur_s >= 3600:
    dur_fmt = f'{dur_s / 3600:.1f}h'
elif dur_s >= 60:
    dur_fmt = f'{dur_s / 60:.0f}min'
else:
    dur_fmt = f'{dur_s:.0f}s'

failure_rate = s['failure_rate']

print(f'=== SESSION SUMMARY: {project} ({since_human}) ===')
print()
print(f'sessions: {total_sessions} ({sessions_detail})')
print(f'tokens: {tokens_fmt}')
print(f'cost (derived): ${s["cost_total"]:.2f}')
print(f'avg_duration: {dur_fmt}')
print(f'failure_rate: {failure_rate:.1%}')
print()

# Intent breakdown with bar chart
intents = s['intent_distribution']
if intents:
    total_intents = sum(intents.values())
    print('intent_breakdown:')
    max_bar = 20
    for intent, count in intents.items():
        pct = count / total_intents
        bar_len = round(pct * max_bar)
        bar = '\u2588' * bar_len
        print(f'  {intent:<14}{bar:<{max_bar+2}}{pct:.0%}')
    print()

# Top tools
tools = s['tool_usage']
if tools:
    top5 = list(tools.items())[:5]
    print('top_tools: ' + ', '.join(f'{n} ({c})' for n, c in top5))

# Top models
models = s['top_models']
if models:
    top3 = list(models.items())[:3]
    print('top_models: ' + ', '.join(f'{n} ({c})' for n, c in top3))

print()
print('patterns:')

# Pattern detection
if intents:
    top_intent = next(iter(intents))
    top_pct = list(intents.values())[0] / total_intents
    if top_intent == 'mixed-work' and top_pct > 0.4:
        print('  \u26a0 High mixed-work intent \u2014 consider more specific task framing')
    elif top_pct > 0.6:
        print(f'  \u26a0 Dominated by {top_intent} ({top_pct:.0%}) \u2014 consider specialized crew')

if failure_rate < 0.1:
    print(f'  \u2713 Low failure rate ({failure_rate:.1%}) \u2014 tools well-configured')
elif failure_rate > 0.3:
    print(f'  \u26a0 High failure rate ({failure_rate:.1%}) \u2014 check tool configuration')

if dur_s > 2400:
    print(f'  \u26a0 Long avg sessions ({dur_fmt}) \u2014 consider task decomposition')
elif dur_s > 0:
    print(f'  \u2713 Reasonable session length ({dur_fmt})')

print()

# Crew recommendation
INTENT_TO_CREW = {
    'bugs': 'bug-fix', 'features': 'general', 'refactoring': 'general',
    'testing': 'bug-fix', 'infrastructure': 'infrastructure',
    'research': 'research', 'documentation': 'research',
    'mixed-work': 'general',
}
crews = set()
if intents:
    for intent, count in intents.items():
        pct = count / total_intents
        if pct >= 0.15:
            crews.add(INTENT_TO_CREW.get(intent, 'general'))
crews.add('general')
crews_list = sorted(crews)
print(f'crew_recommendation: [{", ".join(crews_list)}]')

# Reason
if len(crews_list) == 1:
    top_intent = next(iter(intents)) if intents else 'mixed-work'
    print(f'reason: Primary intent is {top_intent}. No strong signal for specialized crews.')
else:
    specialized = [c for c in crews_list if c != 'general']
    print(f'reason: Strong signal for {", ".join(specialized)} based on intent distribution.')
PYEOF
