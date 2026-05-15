#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Release script for agent-crews.

Usage:
    uv run scripts/release.py <major|minor|patch> [--push] [--dry-run]

Steps:
    1. Validates [Unreleased] section has content
    2. Checks for tag conflicts
    3. Computes new version from version.txt + bump type
    4. Moves [Unreleased] content to new version section with today's date
    5. Updates comparison links
    6. Writes new version to version.txt
    7. Commits and tags (atomic — rolls back commit if tag fails)
    8. Optionally pushes (--push flag)
"""

import argparse
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
    return bool(re.search(r"###\s+\w+\n+\s*-\s+", section))


def tag_exists(tag: str) -> bool:
    """Check if a git tag already exists."""
    result = subprocess.run(["git", "tag", "-l", tag], capture_output=True, text=True, cwd=ROOT)
    return tag in result.stdout.strip().split("\n")


def main():
    parser = argparse.ArgumentParser(description="Cut a release")
    parser.add_argument("bump", choices=["major", "minor", "patch"])
    parser.add_argument("--push", action="store_true", help="Push commit and tag after release")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    args = parser.parse_args()

    # Read current state
    major, minor, patch = read_version()
    old_version = f"{major}.{minor}.{patch}"
    new_major, new_minor, new_patch = bump_version(major, minor, patch, args.bump)
    new_version = f"{new_major}.{new_minor}.{new_patch}"
    new_tag = f"v{new_version}"

    # Pre-flight checks
    changelog = CHANGELOG_FILE.read_text()
    if not validate_unreleased(changelog):
        sys.exit("\n❌ [Unreleased] section is empty. Nothing to release.\n"
                 "Add changelog entries before running release.")

    if tag_exists(new_tag):
        sys.exit(f"\n❌ Tag {new_tag} already exists. Delete it first or choose a different bump.")

    # Check working tree is clean (except CHANGELOG.md and version.txt which we'll modify)
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=ROOT)
    dirty = [l for l in result.stdout.strip().split("\n") if l.strip()]
    if dirty:
        sys.exit(f"\n❌ Working tree is not clean. Commit or stash changes first.\n"
                 f"  {len(dirty)} file(s) modified.")

    today = date.today().isoformat()

    # Prepare changelog changes
    new_changelog = changelog.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{new_version}] - {today}",
        1
    )

    # Update comparison links
    unreleased_link = f"[Unreleased]: {REPO_URL}/compare/{new_tag}...HEAD"
    new_version_link = f"[{new_version}]: {REPO_URL}/compare/v{old_version}...{new_tag}"
    new_changelog = re.sub(
        r"\[Unreleased\]:.*",
        f"{unreleased_link}\n{new_version_link}",
        new_changelog,
        count=1
    )

    # Dry run: show what would happen
    if args.dry_run:
        print(f"\n📝 Dry run: {old_version} → {new_version} ({args.bump})")
        print(f"   Tag: {new_tag}")
        print(f"   Date: {today}")
        print(f"   CHANGELOG.md: [Unreleased] → [{new_version}] - {today}")
        print(f"   version.txt: {old_version} → {new_version}")
        if args.push:
            print(f"   Would push commit + tag to origin")
        else:
            print(f"   Would NOT push (use --push to auto-push)")
        print(f"\n   No changes made.")
        return

    # Write files
    CHANGELOG_FILE.write_text(new_changelog)
    VERSION_FILE.write_text(f"{new_version}\n")

    # Atomic commit + tag (rollback commit if tag fails)
    try:
        subprocess.run(["git", "add", "CHANGELOG.md", "version.txt"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", f"chore(release): {new_version}"], cwd=ROOT, check=True)
    except subprocess.CalledProcessError as e:
        # Restore files
        CHANGELOG_FILE.write_text(changelog)
        VERSION_FILE.write_text(f"{old_version}\n")
        sys.exit(f"\n❌ Commit failed: {e}\n   Files restored.")

    try:
        subprocess.run(["git", "tag", new_tag, "-m", f"Release {new_version}"], cwd=ROOT, check=True)
    except subprocess.CalledProcessError as e:
        # Rollback the commit
        subprocess.run(["git", "reset", "--soft", "HEAD~1"], cwd=ROOT)
        subprocess.run(["git", "restore", "--staged", "."], cwd=ROOT)
        CHANGELOG_FILE.write_text(changelog)
        VERSION_FILE.write_text(f"{old_version}\n")
        sys.exit(f"\n❌ Tag creation failed: {e}\n   Commit rolled back. Files restored.")

    # Verify
    if not tag_exists(new_tag):
        subprocess.run(["git", "reset", "--soft", "HEAD~1"], cwd=ROOT)
        subprocess.run(["git", "restore", "--staged", "."], cwd=ROOT)
        CHANGELOG_FILE.write_text(changelog)
        VERSION_FILE.write_text(f"{old_version}\n")
        sys.exit(f"\n❌ Tag {new_tag} not found after creation. Rolled back.")

    print(f"\n✅ Released {new_version}")
    print(f"   {old_version} → {new_version} ({args.bump})")
    print(f"   Tag: {new_tag}")
    print(f"   CHANGELOG.md updated")
    print(f"   version.txt updated")

    if args.push:
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
        subprocess.run(["git", "push", "--tags"], cwd=ROOT, check=True)
        print(f"   Pushed to remote")
    else:
        print(f"\n   Run `git push && git push --tags` to publish.")


if __name__ == "__main__":
    main()
