"""Core build logic: merge configs and generate agent JSON files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from _lib import deep_merge, get_architypes
from _lib.skills import archetype_skill_refs, load_manifest
from _lib.validate import validate_hierarchy


def build_agent(workflow_cfg: dict, archetype_cfg: dict, agent_cfg: dict) -> dict:
    """Merge workflow → archetype → agent config into a kiro agent JSON."""
    MERGE_FIELDS = ["tools", "allowedTools", "toolsSettings", "resources", "hooks", "mcpServers"]
    AGENT_ONLY = ["name", "keyboardShortcut", "welcomeMessage"]

    merged = {}
    for field in MERGE_FIELDS:
        if field in workflow_cfg:
            merged[field] = workflow_cfg[field]

    for field in MERGE_FIELDS:
        if field in archetype_cfg:
            if field in ("tools", "allowedTools"):
                merged[field] = archetype_cfg[field]
            elif field in merged:
                if isinstance(merged[field], list):
                    seen = set()
                    deduped = []
                    for item in merged[field] + archetype_cfg[field]:
                        s = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                        if s not in seen:
                            seen.add(s)
                            deduped.append(item)
                    merged[field] = deduped
                elif isinstance(merged[field], dict):
                    merged[field] = deep_merge(merged[field], archetype_cfg[field])
            else:
                merged[field] = archetype_cfg[field]

    for field in MERGE_FIELDS:
        if field in agent_cfg:
            if field in ("tools", "allowedTools", "toolsSettings"):
                merged[field] = agent_cfg[field]
            elif field in merged:
                if isinstance(merged[field], list):
                    seen = set()
                    deduped = []
                    for item in merged[field] + agent_cfg[field]:
                        s = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                        if s not in seen:
                            seen.add(s)
                            deduped.append(item)
                    merged[field] = deduped
                elif isinstance(merged[field], dict):
                    merged[field] = deep_merge(merged[field], agent_cfg[field])
            else:
                merged[field] = agent_cfg[field]

    agent_json = {"name": agent_cfg["name"]}

    if "description" in agent_cfg:
        agent_json["description"] = agent_cfg["description"]

    prompts = []
    if "prompt" in archetype_cfg:
        prompts.append(archetype_cfg["prompt"].strip())
    if "prompt" in agent_cfg:
        prompts.append(agent_cfg["prompt"].strip())
    if prompts:
        agent_json["prompt"] = "\n\n".join(prompts)

    for field in MERGE_FIELDS:
        if field in merged:
            agent_json[field] = merged[field]

    if "toolsSettings" in agent_json and "tools" in agent_json:
        agent_tools = set(agent_json["tools"])
        tool_aliases = {
            "fs_write": {"write", "fs_write", "fsWrite"},
            "fs_read": {"read", "fs_read", "fsRead"},
            "execute_bash": {"shell", "execute_bash", "execute_cmd"},
            "subagent": {"subagent", "agent_crew", "use_subagent", "crew"},
        }
        pruned = {}
        for setting_key, setting_val in agent_json["toolsSettings"].items():
            aliases = tool_aliases.get(setting_key, {setting_key})
            if aliases & agent_tools:
                pruned[setting_key] = setting_val
        agent_json["toolsSettings"] = pruned
        if not agent_json["toolsSettings"]:
            del agent_json["toolsSettings"]

    for field in AGENT_ONLY:
        if field in agent_cfg and field != "name":
            agent_json[field] = agent_cfg[field]

    if "welcomeMessageSuffix" in workflow_cfg and "welcomeMessage" in agent_json:
        agent_json["welcomeMessage"] += "\n" + workflow_cfg["welcomeMessageSuffix"].strip()

    agent_name = agent_cfg["name"]
    agent_str = json.dumps(agent_json)
    agent_str = agent_str.replace("{{agent_name}}", agent_name)
    agent_json = json.loads(agent_str)

    return agent_json


def resolve_extends(crew: dict, crew_path: Path) -> dict:
    """Resolve extends: field by loading base crew and applying overrides."""
    extends = crew.get("extends")
    if not extends:
        return crew

    root = Path(__file__).parent.parent
    base_path = root / extends
    if not base_path.exists():
        print(f"  ⚠️  extends: '{extends}' not found (from {crew_path})", file=sys.stderr)
        return crew

    with open(base_path, encoding="utf-8") as f:
        try:
            base = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"  ⚠️  extends: YAML parse error in '{extends}': {e}", file=sys.stderr)
            return crew

    if not base:
        print(f"  ⚠️  extends: '{extends}' is empty (from {crew_path})", file=sys.stderr)
        return crew

    remove_agents = set(crew.get("remove_agents", []))

    if "scope" in crew:
        base["scope"] = crew["scope"]

    for key in ("tools", "allowedTools", "toolsSettings", "resources", "hooks"):
        if key in crew:
            base[key] = crew[key]

    override_agents = {}
    for archetype in get_architypes(crew):
        for agent_cfg in archetype.get("agents", []):
            override_agents[agent_cfg["name"]] = (archetype.get("type", "worker"), agent_cfg)

    for archetype in get_architypes(base):
        archetype["agents"] = [
            a for a in archetype.get("agents", [])
            if a["name"] not in remove_agents and a["name"] not in override_agents
        ]

    for _agent_name, (agent_type, agent_cfg) in override_agents.items():
        placed = False
        for archetype in get_architypes(base):
            if archetype.get("type") == agent_type:
                archetype["agents"].append(agent_cfg)
                placed = True
                break
        if not placed:
            key = "architypes" if "architypes" in base else "archetypes" if "archetypes" in base else "architypes"
            base.setdefault(key, []).append({
                "type": agent_type,
                "agents": [agent_cfg],
            })

    archetypes_key = "architypes" if "architypes" in base else "archetypes"
    base[archetypes_key] = [a for a in get_architypes(base) if a.get("agents")]

    base.pop("extends", None)
    base.pop("remove_agents", None)

    return base


def generate(crew_path: Path, output_dir: Path, dry_run: bool = False, sibling_crews=None):
    """Parse crew.yaml and generate agent JSON files."""
    with open(crew_path, encoding="utf-8") as f:
        try:
            crew = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"  ⚠️  Skipping {crew_path}: YAML parse error: {e}", file=sys.stderr)
            return []

    if not crew:
        print(f"  ⚠️  Skipping {crew_path}: empty or invalid YAML", file=sys.stderr)
        return []

    crew = resolve_extends(crew, crew_path)
    validate_hierarchy(crew_path, crew)

    workflow_cfg = {k: v for k, v in crew.items() if k not in ("architypes", "archetypes")}
    agents_generated = []
    manifest = load_manifest()

    crew_agent_names = []
    for archetype in get_architypes(crew):
        for agent_cfg in archetype.get("agents", []):
            crew_agent_names.append(agent_cfg["name"])

    for archetype in get_architypes(crew):
        archetype_cfg = {k: v for k, v in archetype.items() if k not in ("agents", "type")}
        is_orchestrator = archetype.get("type") in ("orchestrator", "dispatcher")
        is_dispatcher = archetype.get("type") == "dispatcher"

        for agent_cfg in archetype.get("agents", []):
            agent_json = build_agent(workflow_cfg, archetype_cfg, agent_cfg)

            if is_orchestrator and "subagent" in agent_json.get("tools", []):
                if not is_dispatcher:
                    ts = agent_json.setdefault("toolsSettings", {})
                    sub = ts.setdefault("subagent", {})
                    if "availableAgents" not in sub:
                        crew_workers = [n for n in crew_agent_names if n != agent_json["name"]]
                        sub["availableAgents"] = crew_workers
                        sub["trustedAgents"] = crew_workers

                if not is_dispatcher:
                    worker_lines = ["\n\n## Your Workers\n",
                                    "| Agent | Role | Dispatch when... |",
                                    "|-------|------|-------------------|"]
                    for arch2 in get_architypes(crew):
                        if arch2.get("type") in ("orchestrator", "dispatcher"):
                            continue
                        for a in arch2.get("agents", []):
                            desc = a.get("description", "")
                            role = re.sub(r"^\[[\w\s-]+\]\s*", "", desc)
                            routes = a.get("routes", "")
                            worker_lines.append(f"| {a['name']} | {role} | {routes} |")
                    if len(worker_lines) > 3:
                        worker_lines.append("")
                        worker_lines.append("If a worker reports BLOCKED needing user input, relay the question directly — don't guess the answer.")
                        agent_json["prompt"] = agent_json.get("prompt", "") + "\n".join(worker_lines)

                routing_lines = ["\n\n## Routing Table\n",
                                 "| Agent | Send work when... |",
                                 "|-------|-------------------|"]
                for arch2 in get_architypes(crew):
                    for a in arch2.get("agents", []):
                        routes = a.get("routes", "")
                        if routes and a["name"] != agent_json["name"]:
                            routing_lines.append(f"| {a['name']} | {routes} |")
                if len(routing_lines) > 3:
                    agent_json["prompt"] = agent_json.get("prompt", "") + "\n".join(routing_lines)

                if sibling_crews and "## Handoff Awareness" not in agent_json.get("prompt", ""):
                    workflow_name = crew.get("workflow", "")
                    siblings = [s for s in sibling_crews if s["workflow"] != workflow_name]
                    if siblings:
                        refuses = set(crew.get("scope", {}).get("refuses", []))
                        siblings.sort(key=lambda s: (-len(refuses & set(s.get("handles", []))), s["workflow"]))
                        lines = []
                        for s in siblings:
                            handles = s.get("description") or (", ".join(s["handles"]) if s.get("handles") else s["workflow"])
                            lines.append(f'- {handles} → "/agent {s["lead"]}"')
                        agent_json["prompt"] = agent_json.get("prompt", "") + \
                            "\n\n## Handoff Awareness\nWhen work shifts outside your scope, suggest switching. Include a 2-3 sentence context summary the user can share with the target agent:\n" + "\n".join(lines)

                refuses_list = crew.get("scope", {}).get("refuses", [])
                if refuses_list and "## Scope Boundary" not in agent_json.get("prompt", ""):
                    if sibling_crews:
                        sibling_handles = set()
                        workflow_name = crew.get("workflow", "")
                        for s in sibling_crews:
                            if s["workflow"] != workflow_name:
                                sibling_handles.update(s.get("handles", []))
                        active_refuses = [r for r in refuses_list if r in sibling_handles]
                    else:
                        active_refuses = refuses_list
                    if active_refuses:
                        boundary_lines = "\n".join(f"- {r}" for r in active_refuses)
                        agent_json["prompt"] = agent_json.get("prompt", "") + \
                            f"\n\n## Scope Boundary\nDo NOT attempt work in these areas — suggest a handoff instead:\n{boundary_lines}"

                prompts_dir = output_dir.parent / "prompts"
                if "welcomeMessage" in agent_json and prompts_dir.is_dir():
                    prompt_entries = []
                    for pf in sorted(prompts_dir.glob("*.md")):
                        if pf.stem == "crew-sheet":
                            continue
                        text = pf.read_text(encoding="utf-8")
                        p_name, p_desc = pf.stem, ""
                        if text.startswith("---"):
                            parts = text.split("---", 2)
                            if len(parts) >= 3:
                                fm = yaml.safe_load(parts[1])
                                if fm:
                                    p_name = fm.get("name", pf.stem)
                                    p_desc = fm.get("description", "")
                        if not p_desc:
                            for line in text.splitlines():
                                if line.strip() and not line.startswith("---"):
                                    p_desc = line.strip()
                                    break
                        if f"@{p_name}" not in agent_json["welcomeMessage"]:
                            prompt_entries.append(f"`@{p_name}` — {p_desc}")
                    if prompt_entries:
                        agent_json["welcomeMessage"] += "\n\n📎 Prompts:\n" + "\n".join(prompt_entries)

            if not is_orchestrator:
                agent_json.setdefault("resources", []).extend(
                    archetype_skill_refs("worker", manifest)
                )
            elif is_orchestrator and not is_dispatcher:
                agent_json.setdefault("resources", []).extend(
                    archetype_skill_refs("orchestrator", manifest)
                )

            name = agent_json["name"]
            out_path = output_dir / f"{name}.json"

            if dry_run:
                print(f"  Would write: {out_path}")
                print(f"    tools: {agent_json.get('tools', [])}")
            else:
                with open(out_path, "w") as f:
                    json.dump(agent_json, f, indent=2)
                    f.write("\n")

            agents_generated.append(name)

    return agents_generated
