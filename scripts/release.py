#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Release script for agent-crews.

Usage:
    uv run scripts/release.py <major|minor|patch> [--push]

Steps:
    1. Validates [Unreleased] section has content
    2. Computes new version from version.txt + bump type
    3. Moves [Unreleased] content to new version section with today's date
    4. Updates comparison links
    5. Writes new version to version.txt
    6. Commits and tags
    7. Optionally pushes (--push flag)
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
VERSION_FILE = ROOT / "version.txt"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
REPO_URL = "https://github.com/smileynet/agent-crews"


def read_version() -> tuple[int, int, int]:
    text = VERSION_FILE.read_text().strip()
    parts = text.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump_version(major: int, minor: int, patch: int, bump: str) -> tuple[int, int, int]:
    if bump == "major":
        return major + 1, 0, 0
    elif bump == "minor":
        return major, minor + 1, 0
    elif bump == "patch":
        return major, minor, patch + 1
    else:
        sys.exit(f"Invalid bump type: {bump}. Use major, minor, or patch.")


def validate_unreleased(content: str) -> bool:
    """Check that [Unreleased] section has actual entries."""
    match = re.search(r"## \[Unreleased\]\n(.*?)(?=\n## \[|\Z)", content, re.DOTALL)
    if not match:
        return False
    section = match.group(1).strip()
    # Must have at least one ### category with content
    return bool(re.search(r"###\s+\w+\n+\s*-\s+", section))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cut a release")
    parser.add_argument("bump", choices=["major", "minor", "patch"])
    parser.add_argument("--push", action="store_true", help="Push commit and tag after release")
    args = parser.parse_args()

    # Read current state
    major, minor, patch = read_version()
    old_version = f"{major}.{minor}.{patch}"
    new_major, new_minor, new_patch = bump_version(major, minor, patch, args.bump)
    new_version = f"{new_major}.{new_minor}.{new_patch}"

    # Read and validate changelog
    changelog = CHANGELOG_FILE.read_text()
    if not validate_unreleased(changelog):
        sys.exit("\n❌ [Unreleased] section is empty. Nothing to release.\n"
                 "Add changelog entries before running release.")

    today = date.today().isoformat()

    # Replace [Unreleased] header with versioned header, add fresh Unreleased
    changelog = changelog.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{new_version}] - {today}",
        1
    )

    # Update comparison links
    unreleased_link = f"[Unreleased]: {REPO_URL}/compare/v{new_version}...HEAD"
    new_version_link = f"[{new_version}]: {REPO_URL}/compare/v{old_version}...v{new_version}"

    # Replace existing unreleased link
    changelog = re.sub(
        r"\[Unreleased\]:.*",
        f"{unreleased_link}\n{new_version_link}",
        changelog,
        count=1
    )

    # Write files
    CHANGELOG_FILE.write_text(changelog)
    VERSION_FILE.write_text(f"{new_version}\n")

    print(f"\n✅ Release {new_version}")
    print(f"   {old_version} → {new_version} ({args.bump})")
    print(f"   CHANGELOG.md updated")
    print(f"   version.txt updated")

    # Commit and tag
    subprocess.run(["git", "add", "CHANGELOG.md", "version.txt"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"chore(release): {new_version}"], cwd=ROOT, check=True)
    subprocess.run(["git", "tag", f"v{new_version}"], cwd=ROOT, check=True)
    print(f"   Committed and tagged v{new_version}")

    if args.push:
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
        subprocess.run(["git", "push", "--tags"], cwd=ROOT, check=True)
        print(f"   Pushed to remote")
    else:
        print(f"\n   Run `git push && git push --tags` to publish.")


if __name__ == "__main__":
    main()
