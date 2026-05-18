---
description: "Cut a release — validate, curate changelog, bump version, tag, optionally publish"
---
# Release

Cut a new release of agent-crews.

## Steps

1. Pre-flight checks
   - `just build --all` passes cleanly.
   - `uv run pytest tests/` passes.
   - Working tree clean (commit or stash first).
   - `CHANGELOG.md` `[Unreleased]` section has actual entries under Added / Changed / Fixed / Removed.
2. Review and curate the `[Unreleased]` entries for clarity, dedup, and BREAKING tagging. Group ad-hoc sub-blocks into the canonical four categories.
3. Determine the bump type from the changelog:
   - `major` — breaking changes in a 1.x+ release.
   - `minor` — pre-1.0 breaking changes, or post-1.0 additive features.
   - `patch` — fixes and internal-only changes.
4. Dry-run: `uv run scripts/release.py <bump> --dry-run` and confirm the planned diff.
5. Execute: `uv run scripts/release.py <bump> --push` (omits `--push` to stage locally).

The script writes `version.txt`, updates the `CHANGELOG.md` header + compare links, commits as `chore(release): <version>`, tags `v<version>`, and pushes both when `--push` is set.

## Parameters

- `bump` (required): `major` | `minor` | `patch`.
- `--push` (optional): auto-push commit + tag to `origin`.
- `--dry-run` (optional): show the planned changes without writing.
