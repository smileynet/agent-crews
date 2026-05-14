#!/usr/bin/env bash
# Send notification via Slack webhook
# Usage: notify-slack.sh TITLE MESSAGE
# Requires: SLACK_WEBHOOK env var (set in .mise.local.toml)
set -euo pipefail

TITLE="${1:?Usage: notify-slack.sh TITLE MESSAGE}"
MSG="${2:-}"

if [ -z "${SLACK_WEBHOOK:-}" ]; then
  echo "SLACK_WEBHOOK not set. Add to .mise.local.toml:" >&2
  echo '  [env]' >&2
  echo '  SLACK_WEBHOOK = "https://hooks.slack.com/services/..."' >&2
  exit 1
fi

curl -sf -H "Content-Type: application/json" \
  -d "{\"text\":\"*${TITLE}*: ${MSG}\"}" \
  "$SLACK_WEBHOOK" >/dev/null
