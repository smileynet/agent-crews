"""Sync shared steering, skills, and prompts to project directories."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml


def get_project_persona(kiro_dir: Path) -> str:
    """Read persona field from project crew.yaml. Defaults to 'sa'."""
    crew_file = kiro_dir / "crew.yaml"
    if not crew_file.exists():
        return "sa"
    with open(crew_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        return "sa"
    return data.get("persona", "sa")


def sync_steering_to_project(kiro_dir: Path, root: Path):
    """Sync steering files to a project based on its persona."""
    persona = get_project_persona(kiro_dir)
    steering_root = root / "shared" / "steering"
    dest_steering = kiro_dir / "steering"
    dest_steering.mkdir(parents=True, exist_ok=True)

    expected_files = set()

    universal_dir = steering_root / "universal"
    if universal_dir.is_dir():
        for f in universal_dir.glob("*.md"):
            shutil.copy2(f, dest_steering / f.name)
            expected_files.add(f.name)

    persona_dir = steering_root / persona
    if persona_dir.is_dir():
        for f in persona_dir.glob("*.md"):
            shutil.copy2(f, dest_steering / f.name)
            expected_files.add(f.name)

    # Remove stale files from previous persona sync
    all_shared_files = set()
    for subdir in steering_root.iterdir():
        if subdir.is_dir():
            for f in subdir.glob("*.md"):
                all_shared_files.add(f.name)

    for existing in dest_steering.glob("*.md"):
        if existing.name in all_shared_files and existing.name not in expected_files:
            existing.unlink()


def sync_skills_to_project(kiro_dir: Path, root: Path):
    """Sync shared skills to a project's .kiro/skills/ directory."""
    shared_skills = root / "shared" / "skills"
    if not shared_skills.is_dir():
        return
    dest_skills = kiro_dir / "skills"
    dest_skills.mkdir(parents=True, exist_ok=True)
    for item in shared_skills.iterdir():
        dest = dest_skills / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        elif item.is_file():
            shutil.copy2(item, dest)


def sync_prompts_to_project(kiro_dir: Path, root: Path, workspace: dict | None = None):
    """Sync shared prompts to a project's .kiro/prompts/ directory.

    When `workspace` is supplied, `{{workspace.ephemeral}}` / `{{workspace.durable}}`
    placeholders inside prompt text are substituted with the resolved paths.
    """
    from _lib.workspace import substitute_workspace_placeholders

    shared_prompts = root / "shared" / "prompts"
    if not shared_prompts.is_dir():
        return
    dest_prompts = kiro_dir / "prompts"
    dest_prompts.mkdir(parents=True, exist_ok=True)

    shared_files = {f.name for f in shared_prompts.glob("*.md")}

    for f in shared_prompts.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        if workspace:
            text = substitute_workspace_placeholders(text, workspace)
        (dest_prompts / f.name).write_text(text, encoding="utf-8")

    # Remove stale previously-synced shared prompts
    meta_path = kiro_dir / ".agent-crews-meta.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as mf:
            meta = json.load(mf)
        prev_shared = set(meta.get("shared_prompts", []))
        for stale in prev_shared - shared_files:
            stale_path = dest_prompts / stale
            if stale_path.exists():
                stale_path.unlink()
