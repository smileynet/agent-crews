"""Utility functions: routing table, crew sheet, sibling map, etc."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from _lib import get_architypes


def has_custom_crews(kiro_dir: Path) -> bool:
    """Check if a project has custom crews (should skip syncing)."""
    return (kiro_dir / "crews" / "intake-crew.yaml").exists() or (kiro_dir / ".custom-crews").exists()


def _legacy_project_md_skeleton(name: str) -> str:
    return f"""---
inclusion: always
---

# {name}

<!-- TODO: What is this project? One-two sentence description. -->

## Stack

<!-- TODO: Languages, frameworks, key dependencies -->

## Layout

<!-- TODO: Key directories and what they contain -->
```
```

## Conventions

<!-- TODO: Project-specific conventions that differ from defaults -->

## DO NOT

<!-- TODO: Project-specific safety constraints -->

## Key References

<!-- TODO: Important files agents should know about -->
"""


def _project_md_skeleton(name: str) -> str:
    return f"""---
inclusion: always
---

# {name} — Project Context

## Scope Of This File

- Keep this file short. Include only facts most deployed agents need on most turns.
- Put project/runtime facts here. Put reusable crew behavior in source config, components, skills, or prompts instead.
- If a detail matters only for one task, pass it in the task instead of growing this file.

## Runtime Boundary

- `.kiro/` is the deployed runtime surface for this project: generated agents, prompts, skills, and local steering.
- `.crews/` is the project config surface that defines what gets deployed here.
- If both exist, change `.crews/` or other source inputs, then rebuild. Do not hand-edit generated `.kiro/agents/*.json`.

## What This Project Is

<!-- TODO: What is this project? One-two sentence description. -->

## Stack

<!-- TODO: Languages, frameworks, key dependencies -->

## Layout

<!-- TODO: Key directories and what they contain -->
```
```

## Conventions

<!-- TODO: Project-specific conventions that differ from defaults -->

## DO NOT

<!-- TODO: Project-specific safety constraints -->

## Key References

<!-- TODO: Important files agents should know about -->
"""


def generate_project_md_skeleton(kiro_dir: Path):
    """Create or upgrade the default project.md skeleton."""
    project_md = kiro_dir / "steering" / "project.md"
    project_md.parent.mkdir(parents=True, exist_ok=True)
    name = kiro_dir.parent.name
    content = _project_md_skeleton(name)
    if project_md.exists():
        existing = project_md.read_text(encoding="utf-8")
        if existing != _legacy_project_md_skeleton(name):
            return
    project_md.write_text(content, encoding="utf-8")


def build_sibling_map(crew_files: list[Path]) -> list[dict]:
    """Build sibling crew info from a list of crew YAML paths."""
    siblings = []
    for cf in crew_files:
        with open(cf, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        workflow = data.get("workflow", cf.stem)
        scope = data.get("scope", {}) or {}
        handles = scope.get("handles", [])
        description = scope.get("description", "")
        lead = None
        for arch in get_architypes(data):
            if arch.get("type") == "orchestrator" and arch.get("agents"):
                lead = arch["agents"][0]["name"]
                break
        if lead:
            siblings.append({"workflow": workflow, "handles": handles, "description": description, "lead": lead})
    return siblings


def collect_shared_agents(crew_files: list[Path]) -> list[str]:
    """Collect agent names marked shared: true across all crews."""
    shared = []
    for cf in crew_files:
        try:
            crew = yaml.safe_load(cf.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        for archetype in get_architypes(crew or {}):
            for agent in archetype.get("agents", []):
                if agent.get("shared"):
                    shared.append(agent["name"])
    return shared


def generate_routing_table(crews_dir: Path) -> str:
    """Auto-generate routing table from agents' routes: fields."""
    lines = ["## Routing Table", "",
             "| Agent | Crew | Routes (send work when...) |",
             "|-------|------|---------------------------|"]
    for crew_file in sorted(crews_dir.glob("*.yaml")):
        with open(crew_file, encoding="utf-8") as f:
            crew = yaml.safe_load(f)
        crew_name = crew.get("workflow", crew_file.stem)
        for archetype in get_architypes(crew):
            for agent in archetype.get("agents", []):
                routes = agent.get("routes", "")
                if routes:
                    lines.append(f"| `{agent['name']}` | {crew_name} | {routes} |")
    return "\n".join(lines) + "\n"


def generate_crew_sheet(crews_dir: Path) -> str:
    """Auto-generate crew-sheet.md prompt listing all agents."""
    lines = ["# Crew Sheet", "",
             "All available agents and crews for this project.", ""]

    for crew_file in sorted(crews_dir.glob("*.yaml")):
        with open(crew_file, encoding="utf-8") as f:
            crew = yaml.safe_load(f)
        crew_name = crew.get("workflow", crew_file.stem)

        lines.append(f"## {crew_name.title()}")
        lines.append("")
        lines.append("| Agent | Role | Command |")
        lines.append("|-------|------|---------|")

        for archetype in get_architypes(crew):
            for agent in archetype.get("agents", []):
                name = agent["name"]
                desc = agent.get("description", "")
                role = re.sub(r"^\[[\w\s-]+\]\s*", "", desc)
                shortcut = agent.get("keyboardShortcut", "")
                cmd = f"`/agent {name}`"
                if shortcut:
                    cmd += f" or `{shortcut}`"
                lines.append(f"| {name} | {role} | {cmd} |")
        lines.append("")

    return "\n".join(lines) + "\n"
