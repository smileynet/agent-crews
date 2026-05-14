---
inclusion: always
---
# Notifications Protocol

## Channels
Active channels: toast
Slack channel:  (ID: )

## Policy: completions

| Policy | When to fire |
|--------|-------------|
| completions | Only on task completion (DONE/FAILED) |
| verbose | Completion + significant milestones + blockers |
| silent | Never (notifications disabled) |

## Channel Implementations
| Channel | Mechanism |
|---------|-----------|
| toast | OS-native notification (terminal bell / osascript / notify-send) |
| discord | Webhook POST to configured URL |
| slack | Webhook POST to configured URL |
| email | SMTP or SES to configured address |

## Rules
- Channels are additive (toast + discord, not one-of)
- Fire notifications AFTER signaling (completion sequence step 6)
- Include: task summary, status, duration
- Keep notifications brief — link to full output if needed
- Never include secrets or sensitive data in notifications
