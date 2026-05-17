---
name: changelog-discipline
description: Quality rules for changelog entries. Use when validating, writing, or reviewing changelog content to ensure user-facing value communication.
---

# Changelog Discipline

## Entry Quality Rules

1. **Technology-replacement test:** If you replaced the underlying technology, would the entry still be true? If yes, it describes value. If no, it describes implementation.
2. **Can't-name-a-file test:** If you can't write the entry without naming a file, class, or internal module, it's not user-facing.
3. **Impact over mechanism:** State what changed for the user, not how the code does it.
4. **One entry per logical change:** Group related commits into a single entry.
5. **Active voice, specific words:** "Users can now X" not "X functionality was added."

## Decision Test

| Commit type | Changelog? | Category |
|-------------|:----------:|----------|
| feat | Yes | Added |
| fix | Yes | Fixed |
| perf | Yes | Changed |
| BREAKING CHANGE | Yes | Changed/Removed |
| docs, chore, test, ci, refactor | No | — |

## Good vs Bad Examples

| ✅ Good (user-facing value) | ❌ Bad (developer activity) |
|---|---|
| Projects can now inherit base crews with `extends:` | Added resolve_extends function to generate.py |
| Orchestrator no longer absorbs analysis tasks | Removed read from orchestrator tools list |
| Fixed crash when project has no theme configured | Fixed bug in line 47 of generate.py |
| The `legacyAuth` option is deprecated — migrate to `oauth2` before v3.0 | Deprecated legacyAuth |

## Breaking Change Requirements

- Entry under "Changed" or "Removed" (never just "Added")
- Migration path mandatory: "use X instead" not just "removed Y"
- Deprecation entries must include timeline

## Validation Checklist

When reviewing changelog entries:
- [ ] Entry answers "what changed for someone deploying agent-crews?"
- [ ] No file/function/class names in the entry
- [ ] Category matches commit type (feat→Added, fix→Fixed)
- [ ] Breaking changes have migration path
- [ ] Entry is one concise bullet (not a paragraph)
