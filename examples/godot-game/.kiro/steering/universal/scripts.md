---
inclusion: always
---
# Available Scripts

| Command | Purpose | Usage |
|---------|---------|-------|
| `.kiro/scripts/cache-docs.sh` | Cache external documentation locally for search (tries llms.txt first) | `cache-docs.sh URL [NAME]` |
| `.kiro/scripts/notify-toast.sh` | OS-native toast notification | `notify-toast.sh TITLE MESSAGE` |
| `.kiro/scripts/notify-discord.sh` | Discord webhook notification (requires DISCORD_WEBHOOK env var) | `notify-discord.sh TITLE MESSAGE` |
| `.kiro/scripts/notify-slack.sh` | Slack webhook notification (requires SLACK_WEBHOOK env var) | `notify-slack.sh TITLE MESSAGE` |
| `.kiro/scripts/validate-mermaid.sh` | Validate mermaid diagram syntax in markdown files | `validate-mermaid.sh [FILE_OR_DIR]` |
