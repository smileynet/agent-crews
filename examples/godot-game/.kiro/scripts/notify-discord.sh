#!/usr/bin/env bash
# Send notification via Discord webhook
# Usage: notify-discord.sh TITLE MESSAGE
# Requires: DISCORD_WEBHOOK env var (set in .mise.local.toml)
set -euo pipefail

TITLE="${1:?Usage: notify-discord.sh TITLE MESSAGE}"
MSG="${2:-}"

if [ -z "${DISCORD_WEBHOOK:-}" ]; then
  echo "DISCORD_WEBHOOK not set. Add to .mise.local.toml:" >&2
  echo '  [env]' >&2
  echo '  DISCORD_WEBHOOK = "https://discord.com/api/webhooks/..."' >&2
  exit 1
fi

curl -sf -H "Content-Type: application/json" \
  -d "{\"content\":\"**${TITLE}**: ${MSG}\"}" \
  "$DISCORD_WEBHOOK" >/dev/null
