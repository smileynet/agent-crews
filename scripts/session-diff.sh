#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat << 'EOF'
Usage: ./scripts/session-diff.sh <project-path> <before-date> [after-date]
       ./scripts/session-diff.sh <project-path> --since-change <commit>

Compare session performance before and after a crew change.
Dates in YYYY-MM-DD format. After-date defaults to today.

Examples:
  ./scripts/session-diff.sh ~/code/my-project 2026-05-10
  ./scripts/session-diff.sh ~/code/my-project 2026-05-01 2026-05-15
  ./scripts/session-diff.sh ~/code/my-project --since-change b661f19
EOF
  exit 0
}
[[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 2 ]] && show_help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

PROJECT_PATH="$1"
shift

# Handle --since-change: look up date from change markers or git
if [[ "${1:-}" == "--since-change" ]]; then
  COMMIT="${2:-}"
  if [[ -z "$COMMIT" ]]; then echo "Error: --since-change requires a commit SHA"; exit 1; fi
  # Try change-markers.yaml first
  MARKERS_FILE="$REPO_DIR/scratch/change-markers.yaml"
  if [[ -f "$MARKERS_FILE" ]]; then
    BEFORE_DATE=$(grep -A1 "commit: \"$COMMIT\"" "$MARKERS_FILE" | grep "date:" | head -1 | sed 's/.*"\([0-9-]*\)T.*/\1/' || true)
  fi
  # Fall back to git log date
  if [[ -z "${BEFORE_DATE:-}" ]]; then
    BEFORE_DATE=$(git -C "$REPO_DIR" log -1 --pretty=format:'%cd' --date=short "$COMMIT" 2>/dev/null || true)
  fi
  if [[ -z "${BEFORE_DATE:-}" ]]; then echo "Error: cannot resolve date for commit $COMMIT"; exit 1; fi
  AFTER_DATE="$(date +%Y-%m-%d)"
else
  BEFORE_DATE="$1"
  AFTER_DATE="${2:-$(date +%Y-%m-%d)}"
fi

PROJECT_NAME="$(basename "$(realpath "$PROJECT_PATH")")"

# Ingest all sessions for this project
uv run "$REPO_DIR/session-ingest.py" --ingest "$PROJECT_PATH" --project "$PROJECT_PATH" >/dev/null 2>&1

EVENTS_FILE="$REPO_DIR/scratch/sessions/$PROJECT_NAME/all.jsonl"

if [[ ! -f "$EVENTS_FILE" ]]; then
  echo "Error: No session data at $EVENTS_FILE" >&2
  echo "Run: uv run session-ingest.py --ingest $PROJECT_PATH --project $PROJECT_PATH" >&2
  exit 1
fi

export EVENTS_FILE BEFORE_DATE AFTER_DATE PROJECT_NAME

python3 << 'PYEOF'
import json, os, sys
from collections import Counter
from datetime import datetime

events_file = os.environ['EVENTS_FILE']
before_date = os.environ['BEFORE_DATE']
after_date = os.environ['AFTER_DATE']
project = os.environ['PROJECT_NAME']

def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None

# Load and split events by date
before_events, after_events = [], []
with open(events_file) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        date_str = parse_ts(ev.get("timestamp", ""))
        if not date_str:
            continue
        if date_str < before_date:
            before_events.append(ev)
        elif date_str < after_date:
            after_events.append(ev)

def compute_stats(events):
    sessions = set()
    cost = 0.0
    tokens = 0
    tool_results = 0
    tool_errors = 0
    intents = Counter()
    tool_calls = Counter()
    shell_total = 0
    shell_errors = 0
    subagent_calls = 0
    session_times = {}

    for ev in events:
        sid = ev.get("session_id", "")
        sessions.add(sid)
        session_times.setdefault(sid, []).append(ev.get("timestamp", ""))

        if ev.get("cost"):
            cost += ev["cost"]
        if ev.get("tokens_in"):
            tokens += ev["tokens_in"]
        if ev.get("tokens_out"):
            tokens += ev["tokens_out"]

        role = ev.get("role", "")
        if role == "user" and ev.get("content"):
            intents[classify_intent(ev["content"])] += 1
        if role == "assistant" and ev.get("tool_name"):
            tool_calls[ev["tool_name"]] += 1
            if ev["tool_name"] == "shell":
                shell_total += 1
            if ev["tool_name"] in ("subagent", "sub_agent"):
                subagent_calls += 1
        if role == "tool_result":
            tool_results += 1
            output = (ev.get("tool_output") or "").lower()
            if "error" in output or "failed" in output:
                tool_errors += 1
                # Check if this was a shell result
                if ev.get("tool_name") == "shell" or shell_total > 0:
                    shell_errors += 1

    # Compute durations
    durations = []
    for sid, times in session_times.items():
        sorted_t = sorted(t for t in times if t)
        if len(sorted_t) >= 2:
            try:
                start = datetime.fromisoformat(sorted_t[0].replace("Z", "+00:00"))
                end = datetime.fromisoformat(sorted_t[-1].replace("Z", "+00:00"))
                dur = (end - start).total_seconds()
                if dur > 0:
                    durations.append(dur)
            except (ValueError, AttributeError):
                pass

    avg_dur = sum(durations) / len(durations) if durations else 0
    failure_rate = tool_errors / tool_results if tool_results else 0
    shell_fail_rate = shell_errors / shell_total if shell_total else 0

    return {
        "sessions": len(sessions),
        "cost": cost,
        "tokens": tokens,
        "failure_rate": failure_rate,
        "avg_duration_s": avg_dur,
        "intents": dict(intents),
        "shell_fail_rate": shell_fail_rate,
        "subagent_calls": subagent_calls,
    }

def classify_intent(text):
    text_lower = text.lower()
    keywords = {
        "bugs": ["bug", "fix", "broken", "error", "crash", "fail"],
        "features": ["add", "implement", "create", "build", "feature", "new"],
        "refactoring": ["refactor", "restructure", "clean up", "reorganize"],
        "testing": ["test", "spec", "coverage"],
        "infrastructure": ["deploy", "infra", "terraform", "docker", "ci"],
        "research": ["research", "investigate", "analyze", "explore"],
        "documentation": ["doc", "readme", "comment"],
    }
    scores = Counter()
    for intent, kws in keywords.items():
        for kw in kws:
            if kw in text_lower:
                scores[intent] += 1
    return scores.most_common(1)[0][0] if scores else "mixed-work"

def fmt_tokens(t):
    if t >= 1_000_000:
        return f"{t / 1_000_000:.1f}M"
    if t >= 1_000:
        return f"{t / 1_000:.0f}K"
    return str(t)

def fmt_dur(s):
    if s >= 3600:
        return f"{s / 3600:.1f}h"
    if s >= 60:
        return f"{s / 60:.0f}min"
    return f"{s:.0f}s"

def fmt_delta(before_val, after_val, fmt_fn=str, unit="", is_lower_better=True):
    delta = after_val - before_val
    if before_val == 0:
        pct_str = ""
    else:
        pct = abs(delta) / before_val * 100
        direction = "↓" if delta < 0 else "↑"
        pct_str = f" ({direction}{pct:.0f}%)"
    improved = (delta < 0) if is_lower_better else (delta > 0)
    check = " ✓" if improved and abs(delta) > 0 else ""
    sign = "-" if delta < 0 else "+"
    return f"{sign}{fmt_fn(abs(delta))}{unit}{pct_str}{check}"

# Compute
b = compute_stats(before_events)
a = compute_stats(after_events)

if b["sessions"] == 0 and a["sessions"] == 0:
    print(f"No sessions found for {project} around {before_date}")
    sys.exit(1)

# Header
print(f"=== SESSION DIFF: {project} ===")
print(f"Period: before {before_date} vs after {before_date}")
print()

# Main metrics table
hdr = f"{'':20}{'BEFORE':16}{'AFTER':16}DELTA"
print(hdr)

# Sessions
print(f"{'sessions':20}{b['sessions']:<16}{a['sessions']:<16}{fmt_delta(b['sessions'], a['sessions'], str, '', False)}")

# Cost
b_cost_s = f"${b['cost']:.2f}"
a_cost_s = f"${a['cost']:.2f}"
print(f"{'cost':20}{b_cost_s:<16}{a_cost_s:<16}{fmt_delta(b['cost'], a['cost'], lambda v: f'${v:.2f}')}")

# Tokens
print(f"{'tokens':20}{fmt_tokens(b['tokens']):<16}{fmt_tokens(a['tokens']):<16}{fmt_delta(b['tokens'], a['tokens'], fmt_tokens)}")

# Failure rate
b_fr = f"{b['failure_rate']:.0%}"
a_fr = f"{a['failure_rate']:.0%}"
fr_delta = a['failure_rate'] - b['failure_rate']
fr_pct = abs(fr_delta) / b['failure_rate'] * 100 if b['failure_rate'] > 0 else 0
fr_dir = "↓" if fr_delta < 0 else "↑"
fr_check = " ✓" if fr_delta < 0 else ""
fr_sign = "-" if fr_delta < 0 else "+"
fr_delta_str = f"{fr_sign}{abs(fr_delta)*100:.0f}pp ({fr_dir}{fr_pct:.0f}%){fr_check}" if b['failure_rate'] > 0 else f"{fr_sign}{abs(fr_delta)*100:.0f}pp"
print(f"{'failure_rate':20}{b_fr:<16}{a_fr:<16}{fr_delta_str}")

# Avg duration
print(f"{'avg_duration':20}{fmt_dur(b['avg_duration_s']):<16}{fmt_dur(a['avg_duration_s']):<16}{fmt_delta(b['avg_duration_s'], a['avg_duration_s'], fmt_dur)}")

# Intent shift
all_intents = set(list(b['intents'].keys()) + list(a['intents'].keys()))
if all_intents:
    b_total = sum(b['intents'].values()) or 1
    a_total = sum(a['intents'].values()) or 1
    print()
    print("intent_shift:")
    for intent in sorted(all_intents):
        b_pct = b['intents'].get(intent, 0) / b_total * 100
        a_pct = a['intents'].get(intent, 0) / a_total * 100
        direction = "↓" if a_pct < b_pct else "↑"
        print(f"  {intent:<18}{b_pct:.0f}% → {a_pct:.0f}%{' ':6}{direction}")

# Tool shift
print()
print("tool_shift:")
b_sf = f"{b['shell_fail_rate']:.0%}"
a_sf = f"{a['shell_fail_rate']:.0%}"
sf_dir = "↓" if a['shell_fail_rate'] < b['shell_fail_rate'] else "↑"
sf_check = " ✓" if a['shell_fail_rate'] < b['shell_fail_rate'] else ""
print(f"  {'shell failures':<18}{b_sf} → {a_sf}{' ':6}{sf_dir}{sf_check}")

sa_dir = "↑" if a['subagent_calls'] > b['subagent_calls'] else "↓"
sa_check = " ✓" if a['subagent_calls'] > b['subagent_calls'] else ""
print(f"  {'subagent calls':<18}{b['subagent_calls']} → {a['subagent_calls']}{' ':6}{sa_dir}{sa_check}")

# Verdict
print()
cost_down = a['cost'] < b['cost']
failures_down = a['failure_rate'] < b['failure_rate']
delegation_up = a['subagent_calls'] > b['subagent_calls']
duration_up = a['avg_duration_s'] > b['avg_duration_s'] * 1.2  # 20% regression threshold

reasons = []
if cost_down:
    reasons.append("cost down")
if failures_down:
    reasons.append("failures down")
if delegation_up:
    reasons.append("delegation up")

regressions = []
if a['failure_rate'] > b['failure_rate'] * 1.1:
    regressions.append("failure_rate up")
if duration_up:
    regressions.append("duration up")

if (cost_down or failures_down) and not regressions:
    print(f"verdict: ✓ IMPROVED ({', '.join(reasons)})")
elif regressions and not reasons:
    print(f"verdict: ✗ REGRESSED ({', '.join(regressions)})")
elif regressions:
    print(f"verdict: ~ MIXED ({', '.join(reasons)}; but {', '.join(regressions)})")
else:
    print("verdict: — NO CHANGE")
PYEOF
