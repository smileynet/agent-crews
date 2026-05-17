"""Skill manifest loading and resolution.

The manifest at shared/skills/manifest.yaml classifies every skill by how it
reaches agents at runtime:

- `archetype.worker` / `archetype.orchestrator` — auto-injected by `generate`
  into matching agent `resources:` lists.
- `crew_referenced` — declared per-crew/per-agent in YAML; pass-through only.
- `user_only` — synced for `@skill-name` invocation, never auto-loaded.

Skills are referenced from agents as `skill://.kiro/skills/<name>` (single-file)
or `skill://.kiro/skills/<name>/SKILL.md` (multi-file). Both shapes are derived
here from what is on disk under `shared/skills/`.
"""

from __future__ import annotations

from pathlib import Path

import yaml

SHARED_SKILLS = Path(__file__).parent.parent / "shared" / "skills"
MANIFEST_PATH = SHARED_SKILLS / "manifest.yaml"


def list_shared_skills() -> list[str]:
    """Return every skill name available under shared/skills/.

    Both `foo.md` (single-file) and `foo/SKILL.md` (multi-file) layouts
    contribute their base name (`foo`). The manifest itself is excluded.
    """
    if not SHARED_SKILLS.is_dir():
        return []
    names: set[str] = set()
    for entry in SHARED_SKILLS.iterdir():
        if entry.name == "manifest.yaml":
            continue
        if entry.is_dir() and (entry / "SKILL.md").exists():
            names.add(entry.name)
        elif entry.is_file() and entry.suffix == ".md":
            names.add(entry.stem)
    return sorted(names)


def load_manifest() -> dict:
    """Load and return the parsed skill manifest. Empty dict if missing."""
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def manifest_classified_skills(manifest: dict | None = None) -> set[str]:
    """Return every skill name that appears in any manifest section."""
    m = manifest if manifest is not None else load_manifest()
    classified: set[str] = set()
    arch = m.get("archetype") or {}
    for bucket in arch.values():
        classified.update(bucket or [])
    classified.update(m.get("crew_referenced") or [])
    classified.update(m.get("user_only") or [])
    return classified


def skill_reference(name: str) -> str:
    """Resolve a skill name to its `skill://.kiro/skills/...` reference.

    Picks the SKILL.md shape if a multi-file skill exists on disk; otherwise
    falls back to the single-file `.md` shape.
    """
    multi = SHARED_SKILLS / name / "SKILL.md"
    if multi.exists():
        return f"skill://.kiro/skills/{name}/SKILL.md"
    return f"skill://.kiro/skills/{name}.md"


def archetype_skill_refs(archetype: str, manifest: dict | None = None) -> list[str]:
    """Return ordered `skill://` references to auto-inject for an archetype.

    `archetype` is one of `worker`, `orchestrator`. Unknown archetypes return
    an empty list (dispatchers receive no auto-injected skills today).
    """
    m = manifest if manifest is not None else load_manifest()
    names = (m.get("archetype") or {}).get(archetype) or []
    return [skill_reference(n) for n in names]
