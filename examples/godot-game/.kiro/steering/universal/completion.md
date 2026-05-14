---
inclusion: always
---
# Completion Protocol (Standard)

## Sequence (execute in order)
1. **Verification** — confirm all checks pass (gate workflow)
2. **Git** — commit and push verified work:
   - If `git remote get-url origin` succeeds → `git pull --rebase && git push`
   - If NO remote → commit locally, report "No git remote. Committed at [SHA]."
   - Never silently skip push.
3. **Signaling** — emit structured DONE/PARTIAL/BLOCKED/FAILED signal
4. **Followups** — file issues for out-of-scope findings
5. **Handoff** — deliver handoff summary (see elements below)
6. **Notifications** — fire configured channels
7. **Memory** — persist lessons/decisions to appropriate tier

## Handoff Elements (Standard = 5)
1. **Asked → Delivered** — what was requested vs what was produced
2. **State change** — what's different now (before/after)
3. **Files** — what was created/modified/deleted
4. **Issues filed** — follow-up work logged
5. **Next steps** — what to do next (actionable, specific)

## Followups
Default: file issues for anything discovered but out of scope.
Format: one-line title + context for why it matters.

## Secret Handling
If a user pastes a secret (API key, token, PAT):
- Do NOT echo it back. Reference by name only.
- Store in Secrets Manager or `.env` (not in code/commits)
- Warn: "⚠️ I see a secret. I'll reference it by name only."

## Anti-Patterns
- ❌ "Ready to push when you are" — push NOW
- ❌ Marking done without verification evidence
- ❌ Closing without documenting current state
