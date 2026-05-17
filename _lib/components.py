"""Component system: load, configure, and deploy behavioral components."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import yaml

COMPONENTS_DIR = Path(__file__).parent.parent / "shared" / "components"


def resolve_component_config(project_name: str, fleet: dict) -> dict:
    """Resolve component config: fleet defaults → project overrides."""
    from _lib import deep_merge
    defaults = fleet.get("defaults", {}).get("components", {})
    project_cfg = fleet.get("projects", {}).get(project_name, {})
    project_components = project_cfg.get("components", {})
    return deep_merge(defaults, project_components)


def load_component(name: str, config) -> dict:
    """Load a component YAML file. Config is either a string (variant name) or dict with 'variant' key."""
    if isinstance(config, str):
        variant = config
    elif isinstance(config, dict):
        variant = config.get("variant", name)
    else:
        variant = name

    path = COMPONENTS_DIR / name.replace("_", "-") / f"{variant}.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def substitute_placeholders(text: str, config: dict) -> str:
    """Replace {{key.subkey}} placeholders with config values."""

    def _resolve(match):
        key_path = match.group(1)
        if key_path in config:
            val = config[key_path]
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            return str(val) if val is not None else ""
        parts = key_path.split(".")
        val = config
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return match.group(0)
            if val is None:
                return ""
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        return str(val)

    return re.sub(r"\{\{([^}]+)\}\}", _resolve, text)


def load_all_components(component_config: dict) -> list[dict]:
    """Load all declared components and substitute placeholders."""
    components = []
    for name, cfg in component_config.items():
        comp = load_component(name, cfg)
        if not comp:
            continue
        nested = dict(component_config)
        if isinstance(cfg, dict):
            for k, v in cfg.items():
                nested[k] = v

        if comp.get("steering"):
            comp["steering"] = substitute_placeholders(comp["steering"], nested)
        if comp.get("allowed_commands"):
            comp["allowed_commands"] = [
                substitute_placeholders(c, nested) for c in comp["allowed_commands"]
            ]
        components.append(comp)
    return components


def write_steering_files(components: list[dict], kiro_dir: Path):
    """Write .kiro/steering/{universal,orchestrator,worker}/<component>.md from component steering fields."""
    target_dirs = {
        "all": "universal",
        "orchestrator": "orchestrator",
        "worker": "worker",
    }

    for comp in components:
        steering = comp.get("steering")
        if not steering:
            continue
        targets = comp.get("targets", [])
        name = comp.get("name", "unknown").split("-")[0]

        for target in targets:
            subdir = target_dirs.get(target)
            if not subdir:
                continue
            if target == "all":
                dest = kiro_dir / "steering" / "universal" / f"{name}.md"
            else:
                dest = kiro_dir / "steering" / subdir / f"{name}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(steering, encoding="utf-8")


def generate_subagents(components: list[dict], kiro_dir: Path, dry_run: bool = False) -> list[str]:
    """Generate verifier.json, editor.json etc from component subagents: fields."""
    agents_dir = kiro_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    for comp in components:
        for sub in comp.get("subagents", []):
            if not sub:
                continue
            agent_json = {
                "name": sub["name"],
                "description": sub.get("description", ""),
                "tools": sub.get("tools", ["read", "shell"]),
                "allowedTools": sub.get("tools", ["read", "shell"]),
                "prompt": sub.get("prompt", ""),
            }
            if sub.get("resources"):
                agent_json["resources"] = sub["resources"]

            out_path = agents_dir / f"{sub['name']}.json"
            if out_path.exists():
                continue
            if not dry_run:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(agent_json, f, indent=2)
                    f.write("\n")
            generated.append(sub["name"])

    return generated


def deploy_scripts(components: list[dict], kiro_dir: Path, dry_run: bool = False) -> list[dict]:
    """Deploy component scripts to .kiro/scripts/ and return metadata for discovery steering."""
    scripts_dir = kiro_dir / "scripts"
    deployed = []

    for comp in components:
        for script_decl in comp.get("scripts", []):
            if not script_decl:
                continue
            filename = script_decl["file"]
            comp_name = comp.get("name", "unknown")
            comp_dir_name = comp_name.split("-")[0]
            source = COMPONENTS_DIR / comp_dir_name / filename
            if not source.exists():
                continue

            if not dry_run:
                scripts_dir.mkdir(parents=True, exist_ok=True)
                dest = scripts_dir / filename
                shutil.copy2(source, dest)

            deployed.append({
                "file": filename,
                "description": script_decl.get("description", ""),
                "args": script_decl.get("args", ""),
            })

    return deployed


def write_scripts_steering(deployed_scripts: list[dict], kiro_dir: Path):
    """Generate .kiro/steering/universal/scripts.md listing all available scripts."""
    if not deployed_scripts:
        return

    lines = [
        "---",
        "inclusion: always",
        "---",
        "# Available Scripts",
        "",
        "| Command | Purpose | Usage |",
        "|---------|---------|-------|",
    ]
    for s in deployed_scripts:
        cmd = f".kiro/scripts/{s['file']}"
        lines.append(f"| `{cmd}` | {s['description']} | `{s['file']} {s['args']}` |")

    steering_dir = kiro_dir / "steering" / "universal"
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / "scripts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def inject_subagents_into_orchestrators(subagent_names: list[str], kiro_dir: Path):
    """Add component subagents to all orchestrator agents' availableAgents."""
    agents_dir = kiro_dir / "agents"
    if not agents_dir.is_dir():
        return
    for agent_file in agents_dir.glob("*.json"):
        with open(agent_file, encoding="utf-8") as f:
            agent = json.load(f)
        if "subagent" not in agent.get("tools", []):
            continue
        ts = agent.get("toolsSettings", {})
        sub = ts.get("subagent", {})
        available = sub.get("availableAgents", [])
        added = False
        for name in subagent_names:
            if name not in available:
                available.append(name)
                added = True
        if added:
            sub["availableAgents"] = available
            sub.setdefault("trustedAgents", [])
            for name in subagent_names:
                if name not in sub["trustedAgents"]:
                    sub["trustedAgents"].append(name)
            ts["subagent"] = sub
            agent["toolsSettings"] = ts
            with open(agent_file, "w", encoding="utf-8") as f:
                json.dump(agent, f, indent=2)
                f.write("\n")


def merge_allowed_commands(components: list[dict], kiro_dir: Path):
    """Merge component allowed_commands into worker agent toolsSettings."""
    commands = []
    for comp in components:
        targets = comp.get("targets", [])
        if "worker" in targets or "all" in targets:
            commands.extend(comp.get("allowed_commands", []))
    commands = [c for c in commands if c]  # filter empty from null placeholders
    if not commands:
        return
    agents_dir = kiro_dir / "agents"
    if not agents_dir.is_dir():
        return
    for agent_file in agents_dir.glob("*.json"):
        with open(agent_file, encoding="utf-8") as f:
            data = json.load(f)
        if "subagent" in data.get("tools", []):
            continue  # orchestrators don't run commands
        ts = data.setdefault("toolsSettings", {})
        bash = ts.setdefault("execute_bash", {})
        existing = bash.get("allowedCommands", [])
        merged = list(dict.fromkeys(existing + commands))
        bash["allowedCommands"] = merged
        with open(agent_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")


def generate_components_for_project(project_name: str, kiro_dir: Path, fleet: dict, dry_run: bool = False):
    """Full component generation pipeline for a project."""
    component_config = resolve_component_config(project_name, fleet)
    if not component_config:
        return

    components = load_all_components(component_config)
    if not components:
        return

    if not dry_run:
        write_steering_files(components, kiro_dir)
        subagents = generate_subagents(components, kiro_dir, dry_run)
        deployed_scripts = deploy_scripts(components, kiro_dir, dry_run)
        write_scripts_steering(deployed_scripts, kiro_dir)
        merge_allowed_commands(components, kiro_dir)
        if subagents:
            inject_subagents_into_orchestrators(subagents, kiro_dir)
            print(f"    + subagents: {', '.join(subagents)}")
        if deployed_scripts:
            print(f"    + scripts: {len(deployed_scripts)}")
    else:
        print(f"    Would write steering files for {len(components)} components")
