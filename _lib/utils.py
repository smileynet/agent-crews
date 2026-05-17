"""Utility functions: routing table, crew sheet, sibling map, etc."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from _lib import get_architypes


def has_custom_crews(kiro_dir: Path) -> bool:
    """Check if a project has custom crews (should skip syncing)."""
    return (kiro_dir / "crews" / "intake-crew.yaml").exists() or (kiro_dir / ".custom-crews").exists()


def generate_project_md_skeleton(kiro_dir: Path):
    """Generate a skeleton project.md if one doesn't exist."""
    project_md = kiro_dir / "steering" / "project.md"
    if project_md.exists():
        return
    project_md.parent.mkdir(parents=True, exist_ok=True)
    name = kiro_dir.parent.name
    project_md.write_text(f"""---
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
""")


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


def generate_crew_sheet(crews_dir: Path, theme: dict | None = None) -> str:
    """Auto-generate crew-sheet.md prompt listing all agents."""
    lines = ["# Crew Sheet", "",
             "All available agents and crews for this project.", ""]

    agent_map = theme.get("agents", {}) if theme else {}
    name_map = {g: c["name"] for g, c in agent_map.items() if "name" in c}
    crews_cfg = theme.get("crews", {}) if theme else {}

    for crew_file in sorted(crews_dir.glob("*.yaml")):
        with open(crew_file, encoding="utf-8") as f:
            crew = yaml.safe_load(f)
        crew_name = crew.get("workflow", crew_file.stem)

        crew_display = crew_name.title()
        icon = ""
        if crew_name in crews_cfg:
            crew_display = crews_cfg[crew_name].get("display", crew_display)
            icon = crews_cfg[crew_name].get("icon", "")

        header = f"{icon} {crew_display}".strip() if icon else crew_display
        lines.append(f"## {header}")
        lines.append("")
        lines.append("| Agent | Role | Command |")
        lines.append("|-------|------|---------|")

        for archetype in get_architypes(crew):
            for agent in archetype.get("agents", []):
                generic_name = agent["name"]
                display_name = name_map.get(generic_name, generic_name)
                desc = agent.get("description", "")
                role = re.sub(r"^\[[\w\s-]+\]\s*", "", desc)
                shortcut = agent.get("keyboardShortcut", "")
                cmd = f"`/agent {display_name}`"
                if shortcut:
                    cmd += f" or `{shortcut}`"
                lines.append(f"| {display_name} | {role} | {cmd} |")
        lines.append("")

    return "\n".join(lines) + "\n"
