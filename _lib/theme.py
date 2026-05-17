"""Theme overlay: rename agents cosmetically without changing behavior."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

THEMES_DIR = Path(__file__).parent.parent / "shared" / "themes"


def load_theme(theme_name: str) -> dict:
    """Load a theme YAML file from shared/themes/."""
    if not theme_name:
        return {}
    path = THEMES_DIR / f"{theme_name}.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_theme_to_agents(agents_dir: Path, theme: dict):
    """Apply theme overlay: rename agent JSON files and update contents."""
    if not theme:
        return
    agent_map = theme.get("agents", {})
    name_map = {generic: cfg["name"] for generic, cfg in agent_map.items() if "name" in cfg}

    for json_file in sorted(agents_dir.glob("*.json")):
        generic_name = json_file.stem
        if generic_name not in name_map:
            continue

        with open(json_file, encoding="utf-8") as f:
            agent = json.load(f)

        themed_name = name_map[generic_name]
        theme_cfg = agent_map[generic_name]

        agent["name"] = themed_name

        if "welcomeMessage" in theme_cfg:
            agent["welcomeMessage"] = theme_cfg["welcomeMessage"]

        crew_display = _get_crew_display_for_agent(generic_name, theme)
        if crew_display and "description" in agent:
            agent["description"] = re.sub(
                r"^\[[\w\s-]+\]",
                f"[{crew_display}]",
                agent["description"],
            )

        if "prompt" in agent:
            agent["prompt"] = _substitute_names_in_text(agent["prompt"], name_map)

        if "toolsSettings" in agent and "subagent" in agent.get("toolsSettings", {}):
            sub_settings = agent["toolsSettings"]["subagent"]
            for key in ("availableAgents", "trustedAgents"):
                if key in sub_settings:
                    sub_settings[key] = [name_map.get(n, n) for n in sub_settings[key]]

        new_path = agents_dir / f"{themed_name}.json"
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(agent, f, indent=2)
            f.write("\n")

        if json_file.name != new_path.name and json_file.exists():
            json_file.unlink()


def _get_crew_display_for_agent(generic_name: str, theme: dict) -> str:
    """Find the themed crew display name for a given generic agent."""
    crews = theme.get("crews", {})
    prefix_map = {
        "general": ["general-lead", "planner", "explorer", "researcher", "challenger",
                    "advisor", "architect", "builder", "tester", "committer", "reviewer", "advocate"],
        "bug-fix": ["bugfix-lead", "triager", "investigator", "practices-advisor",
                    "reproducer", "fixer", "verifier", "documenter"],
        "infrastructure": ["infrastructure-lead", "deploy-planner", "infra-advisor",
                          "provisioner", "monitor", "security-reviewer", "cleanup"],
        "research": ["research-lead", "outliner", "internal-researcher", "external-researcher",
                    "writer", "fact-checker", "editor"],
        "onboarding": ["onboarding-lead", "mapper", "analyst", "auditor", "restorer", "guide-writer"],
        "hygiene": ["hygiene-lead", "doc-checker", "deps-checker", "structure-checker",
                   "link-checker", "fix-verifier"],
        "content": ["content-lead", "narrative-writer", "content-researcher", "tutorial-writer",
                   "content-reviewer", "publisher"],
        "writing": ["writing-lead", "doc-auditor", "doc-architect", "doc-writer",
                   "tutorial-author", "doc-verifier"],
    }
    for crew_name, agents in prefix_map.items():
        if generic_name in agents:
            crew_cfg = crews.get(crew_name, {})
            icon = crew_cfg.get("icon", "")
            display = crew_cfg.get("display", crew_name.title())
            return f"{icon} {display}".strip() if icon else display
    return ""


def _substitute_names_in_text(text: str, name_map: dict) -> str:
    """Replace generic agent names with themed names in prompt text."""
    for generic, themed in sorted(name_map.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'(?<![a-zA-Z-])' + re.escape(generic) + r'(?![a-zA-Z-])', themed, text)
    return text
