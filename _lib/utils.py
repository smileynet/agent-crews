"""Utility functions: routing table, crew sheet, sibling map, etc."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from _lib import get_architypes


def has_custom_crews(kiro_dir: Path) -> bool:
    """Check if a project has custom crews (should skip syncing)."""
    return (kiro_dir / "crews" / "intake-crew.yaml").exists() or (kiro_dir / ".custom-crews").exists()




def prune_legacy_project_md(kiro_dir: Path):
    """Delete the legacy `steering/project.md` file if it still exists.

    `project.md` was the always-loaded project runtime context until it was retired in
    favor of owner-managed `AGENTS.md`. This is one-shot transition cleanup so old
    deployments converge on rebuild; it can be removed once no live projects carry the
    file anymore.
    """
    legacy = kiro_dir / "steering" / "project.md"
    if legacy.exists():
        legacy.unlink()


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
