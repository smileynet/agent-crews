---
description: "Cut a release — validate, curate changelog, bump version, tag, optionally publish"
---
# Release

Cut a new release of agent-crews.

## Steps

1. Run pre-flight checks (build passes, working tree clean, [Unreleased] has content)
2. Review and curate changelog entries for quality
3. Determine version bump type (major/minor/patch) based on change categories
4. Execute `just release <bump>`
5. Optionally create platform release (`just publish`)

## Parameters

- `bump` (optional): Force a specific bump type. If omitted, agent recommends based on changelog categories.
- `push` (optional): If specified, auto-push after tagging.
