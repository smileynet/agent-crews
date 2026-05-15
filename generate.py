#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Generate .kiro/agents/*.json from a crew.yaml file.

Usage:
    uv run generate.py                    # reads .kiro/crew.yaml, writes .kiro/agents/
    uv run generate.py path/to/crew.yaml  # custom input
    uv run generate.py --dry-run          # print what would be written
    uv run generate.py --all              # generate all projects (sync shared steering + crews to non-custom projects)
    uv run generate.py --sync-steering    # sync shared/steering/ to all projects
    uv run generate.py --sync-prompts     # sync shared/prompts/ to all projects
    uv run generate.py --check-health     # validate allowedCommands vs project.md DO NOTs
"""

import json
import os
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base. Arrays are concatenated and deduped."""
    result = base.copy()
    for key, val in override.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = deep_merge(result[key], val)
            elif isinstance(result[key], list) and isinstance(val, list):
                # Concatenate and deduplicate (preserving order)
                seen = set()
                merged = []
                for item in result[key] + val:
                    s = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                    if s not in seen:
                        seen.add(s)
                        merged.append(item)
                result[key] = merged
            else:
                result[key] = val
        else:
            result[key] = val
    return result


def build_agent(workflow_cfg: dict, archetype_cfg: dict, agent_cfg: dict) -> dict:
    """Merge workflow → archetype → agent config into a kiro agent JSON."""
    # Fields that cascade
    MERGE_FIELDS = ["tools", "allowedTools", "toolsSettings", "resources", "hooks", "mcpServers"]
    AGENT_ONLY = ["name", "keyboardShortcut", "welcomeMessage"]

    # Start with workflow-level defaults
    merged = {}
    for field in MERGE_FIELDS:
        if field in workflow_cfg:
            merged[field] = workflow_cfg[field]

    # Merge archetype level
    # For tools/allowedTools: archetype REPLACES global (not merge)
    # This lets orchestrator restrict to subagent+read only
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

    # Merge agent level
    for field in MERGE_FIELDS:
        if field in agent_cfg:
            if field in ("tools", "allowedTools", "toolsSettings"):
                # Agent-level tools/allowedTools/toolsSettings REPLACE (same as archetype)
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

    # Build final agent JSON
    agent_json = {"name": agent_cfg["name"]}

    if "description" in agent_cfg:
        agent_json["description"] = agent_cfg["description"]

    # Prompt: archetype prompt + agent prompt concatenated
    prompts = []
    if "prompt" in archetype_cfg:
        prompts.append(archetype_cfg["prompt"].strip())
    if "prompt" in agent_cfg:
        prompts.append(agent_cfg["prompt"].strip())
    if prompts:
        agent_json["prompt"] = "\n\n".join(prompts)

    # Merged fields
    for field in MERGE_FIELDS:
        if field in merged:
            agent_json[field] = merged[field]

    # Prune toolsSettings: only keep entries for tools the agent actually has
    if "toolsSettings" in agent_json and "tools" in agent_json:
        agent_tools = set(agent_json["tools"])
        # Map canonical names to aliases for matching
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

    # Agent-only fields
    for field in AGENT_ONLY:
        if field in agent_cfg and field != "name":
            agent_json[field] = agent_cfg[field]

    # Welcome message suffix
    if "welcomeMessageSuffix" in workflow_cfg and "welcomeMessage" in agent_json:
        agent_json["welcomeMessage"] += "\n" + workflow_cfg["welcomeMessageSuffix"].strip()

    # Template substitution: {{agent_name}}
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

    # Resolve base path relative to repo root
    root = Path(__file__).parent
    base_path = root / extends
    if not base_path.exists():
        print(f"  ⚠️  extends: '{extends}' not found (from {crew_path})", file=sys.stderr)
        return crew

    with open(base_path, encoding="utf-8") as f:
        base = yaml.safe_load(f)

    # Start with base, then apply overrides
    remove_agents = set(crew.get("remove_agents", []))

    # Override scope if specified, otherwise inherit
    if "scope" in crew:
        base["scope"] = crew["scope"]

    # Override workflow-level fields if specified
    for key in ("tools", "allowedTools", "toolsSettings", "resources", "hooks"):
        if key in crew:
            base[key] = crew[key]

    # Process architypes: remove agents, add new ones, replace by name
    override_agents = {}  # name -> agent_cfg (from extending crew)
    override_architypes = []  # new architype blocks from extending crew
    for archetype in crew.get("architypes", []):
        for agent_cfg in archetype.get("agents", []):
            override_agents[agent_cfg["name"]] = (archetype.get("type", "worker"), agent_cfg)
        # Collect architype-level config for new agents
        override_architypes.append(archetype)

    # Filter base architypes: remove agents, replace by name
    for archetype in base.get("architypes", []):
        archetype["agents"] = [
            a for a in archetype.get("agents", [])
            if a["name"] not in remove_agents and a["name"] not in override_agents
        ]

    # Add override agents (replacements and new additions) to appropriate architype
    for agent_name, (agent_type, agent_cfg) in override_agents.items():
        # Find matching architype in base, or create one
        placed = False
        for archetype in base.get("architypes", []):
            if archetype.get("type") == agent_type:
                archetype["agents"].append(agent_cfg)
                placed = True
                break
        if not placed:
            # Create new architype block
            base.setdefault("architypes", []).append({
                "type": agent_type,
                "agents": [agent_cfg],
            })

    # Remove empty architypes
    base["architypes"] = [a for a in base.get("architypes", []) if a.get("agents")]

    # Clean up extends-specific keys from result
    base.pop("extends", None)
    base.pop("remove_agents", None)

    return base


def generate(crew_path: Path, output_dir: Path, dry_run: bool = False, sibling_crews=None):
    """Parse crew.yaml and generate agent JSON files."""
    with open(crew_path, encoding="utf-8") as f:
        crew = yaml.safe_load(f)

    # Resolve inheritance if extends: is specified
    crew = resolve_extends(crew, crew_path)

    # Workflow-level config (everything except architypes)
    workflow_cfg = {k: v for k, v in crew.items() if k != "architypes"}

    agents_generated = []

    # Collect all agent names in this crew for subagent scoping
    crew_agent_names = []
    for archetype in crew.get("architypes", []):
        for agent_cfg in archetype.get("agents", []):
            crew_agent_names.append(agent_cfg["name"])

    for archetype in crew.get("architypes", []):
        # Archetype-level config (everything except agents and type)
        archetype_cfg = {k: v for k, v in archetype.items() if k not in ("agents", "type")}
        is_orchestrator = archetype.get("type") == "orchestrator"

        for agent_cfg in archetype.get("agents", []):
            agent_json = build_agent(workflow_cfg, archetype_cfg, agent_cfg)

            # Scope orchestrator subagent access to own crew only
            if is_orchestrator and "subagent" in agent_json.get("tools", []):
                crew_workers = [n for n in crew_agent_names if n != agent_json["name"]]
                ts = agent_json.setdefault("toolsSettings", {})
                ts.setdefault("subagent", {})["availableAgents"] = crew_workers
                ts["subagent"]["trustedAgents"] = crew_workers

                # Auto-inject routing table from routes: fields
                routing_lines = ["\n\n## Routing Table\n",
                                 "| Agent | Send work when... |",
                                 "|-------|-------------------|"]
                for arch2 in crew.get("architypes", []):
                    for a in arch2.get("agents", []):
                        routes = a.get("routes", "")
                        if routes and a["name"] != agent_json["name"]:
                            routing_lines.append(f"| {a['name']} | {routes} |")
                if len(routing_lines) > 3:  # has actual routes
                    agent_json["prompt"] = agent_json.get("prompt", "") + "\n".join(routing_lines)

                # Auto-inject Handoff Awareness from sibling crews
                if sibling_crews and "## Handoff Awareness" not in agent_json.get("prompt", ""):
                    workflow_name = crew.get("workflow", "")
                    siblings = [s for s in sibling_crews if s["workflow"] != workflow_name]
                    if siblings:
                        # Sort by overlap with current crew's refuses (most relevant first)
                        refuses = set(crew.get("scope", {}).get("refuses", []))
                        siblings.sort(key=lambda s: (-len(refuses & set(s.get("handles", []))), s["workflow"]))
                        lines = []
                        for s in siblings:
                            handles = s.get("description") or (", ".join(s["handles"]) if s.get("handles") else s["workflow"])
                            lines.append(f'- {handles} → "/agent {s["lead"]}"')
                        agent_json["prompt"] = agent_json.get("prompt", "") + \
                            "\n\n## Handoff Awareness\nWhen work shifts outside your scope, suggest switching. Include a 2-3 sentence context summary the user can share with the target agent:\n" + "\n".join(lines)

                # Auto-inject Scope Boundary from refuses (only for intents a sibling handles)
                refuses_list = crew.get("scope", {}).get("refuses", [])
                if refuses_list and "## Scope Boundary" not in agent_json.get("prompt", ""):
                    # Filter: only refuse intents that a present sibling actually handles
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

                # Auto-inject available prompts into welcomeMessage
                prompts_dir = output_dir.parent / "prompts"
                if "welcomeMessage" in agent_json and prompts_dir.is_dir():
                    prompt_entries = []
                    for pf in sorted(prompts_dir.glob("*.md")):
                        if pf.stem == "crew-sheet":
                            continue
                        # Extract name/description from YAML frontmatter
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


def has_custom_crews(kiro_dir: Path) -> bool:
    """Check if a project has custom crews (should skip syncing)."""
    return (kiro_dir / "crews" / "intake-crew.yaml").exists() or (kiro_dir / ".custom-crews").exists()


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

    # Collect which files SHOULD exist (from universal + persona dirs)
    expected_files = set()

    # Always sync universal steering
    universal_dir = steering_root / "universal"
    if universal_dir.is_dir():
        for f in universal_dir.glob("*.md"):
            shutil.copy2(f, dest_steering / f.name)
            expected_files.add(f.name)

    # Sync persona-specific steering
    persona_dir = steering_root / persona
    if persona_dir.is_dir():
        for f in persona_dir.glob("*.md"):
            shutil.copy2(f, dest_steering / f.name)
            expected_files.add(f.name)

    # Remove stale files that came from a previous persona sync
    # (but preserve project.md and any project-specific files not in shared/)
    all_shared_files = set()
    for subdir in steering_root.iterdir():
        if subdir.is_dir():
            for f in subdir.glob("*.md"):
                all_shared_files.add(f.name)

    for existing in dest_steering.glob("*.md"):
        if existing.name in all_shared_files and existing.name not in expected_files:
            existing.unlink()


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


def sync_prompts_to_project(kiro_dir: Path, root: Path):
    """Sync shared prompts to a project's .kiro/prompts/ directory."""
    shared_prompts = root / "shared" / "prompts"
    if not shared_prompts.is_dir():
        return
    dest_prompts = kiro_dir / "prompts"
    dest_prompts.mkdir(parents=True, exist_ok=True)

    shared_files = {f.name for f in shared_prompts.glob("*.md")}

    # Copy all shared prompts to project
    for f in shared_prompts.glob("*.md"):
        shutil.copy2(f, dest_prompts / f.name)

    # Remove stale: read provenance to find previously-synced shared prompts
    meta_path = kiro_dir / ".agent-crews-meta.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        prev_shared = set(meta.get("shared_prompts", []))
        for stale in prev_shared - shared_files:
            stale_path = dest_prompts / stale
            if stale_path.exists():
                stale_path.unlink()


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
        # Find orchestrator: first agent in first archetype with type == "orchestrator"
        lead = None
        for arch in data.get("architypes", []):
            if arch.get("type") == "orchestrator" and arch.get("agents"):
                lead = arch["agents"][0]["name"]
                break
        if lead:
            siblings.append({"workflow": workflow, "handles": handles, "description": description, "lead": lead})
    return siblings


def validate_coverage(fleet: dict):
    """Warn about refused keywords that no assigned sibling crew handles.
    
    Only warns when at least one sibling crew's handles list contains a keyword
    in the same domain, suggesting a vocabulary mismatch. Deliberately missing
    crews (no sibling assigned for that domain) are not flagged.
    """
    root = Path(__file__).parent
    base_crews_dir = root / "base" / "crews"
    for proj_name, proj_cfg in fleet.get("projects", {}).items():
        if proj_cfg.get("self_hosted"):
            continue
        crew_names = proj_cfg.get("crews") or fleet.get("defaults", {}).get("crews", [])
        if not crew_names:
            continue
        crew_files = []
        for cn in crew_names:
            local = root / "projects" / proj_name / ".kiro" / "crews" / f"{cn}.yaml"
            base = base_crews_dir / f"{cn}.yaml"
            if local.exists():
                crew_files.append(local)
            elif base.exists():
                crew_files.append(base)
        # Build per-crew scope data
        crews = []
        for cf in crew_files:
            with open(cf, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            scope = data.get("scope", {}) or {}
            crews.append({
                "workflow": data.get("workflow", cf.stem),
                "handles": set(scope.get("handles", [])),
                "refuses": scope.get("refuses", []),
            })
        # For each refused keyword, check if a sibling handles it
        for crew in crews:
            sibling_handles = set()
            for other in crews:
                if other["workflow"] != crew["workflow"]:
                    sibling_handles.update(other["handles"])
            if not sibling_handles:
                continue
            for refused in crew["refuses"]:
                if refused not in sibling_handles:
                    similar = [h for h in sibling_handles if refused in h or h in refused]
                    if similar:
                        print(f"  ⚠️  {proj_name}: '{refused}' refused by {crew['workflow']} — possible vocab mismatch with: {', '.join(similar)}", file=sys.stderr)


def generate_vocabulary(kiro_dir: Path, dry_run: bool = False):
    """Generate project-specific vocabulary.md from assigned crew YAMLs."""
    crews_dir = kiro_dir / "crews"
    if not crews_dir.is_dir():
        return
    crew_files = sorted(crews_dir.glob("*.yaml"))
    if not crew_files:
        return

    # Collect scope data from each crew
    crews = []
    for cf in crew_files:
        with open(cf, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        scope = data.get("scope", {}) or {}
        crews.append({
            "workflow": data.get("workflow", cf.stem),
            "handles": scope.get("handles", []),
            "refuses": scope.get("refuses", []),
        })

    # Build vocabulary table
    lines = [
        "---",
        "inclusion: always",
        "---",
        "",
        "# Vocabulary",
        "",
        "Canonical intent keywords for this project's crews. Use these exact terms in routing and scope decisions.",
        "",
        "| Keyword | Crew | Role |",
        "|---------|------|------|",
    ]
    for crew in crews:
        for h in crew["handles"]:
            lines.append(f"| {h} | {crew['workflow']} | handles |")
    for crew in crews:
        for r in crew["refuses"]:
            lines.append(f"| {r} | {crew['workflow']} | refuses |")

    lines.append("")

    if not dry_run:
        dest = kiro_dir / "steering"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "vocabulary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_all(dry_run: bool = False):
    """Sync crews+steering from base to all projects, then generate all."""
    root = Path(__file__).parent
    base_crews = root / "base" / "crews"
    examples = root / "projects"

    # Load fleet config for component generation
    fleet = load_fleet_config()

    # Sync to each project (projects/ for real, examples/ for reference)
    project_dirs = list(examples.glob("*/.kiro")) + list((root / "examples").glob("*/.kiro"))
    for kiro_dir in sorted(project_dirs):
        proj = kiro_dir.parent.name
        persona = get_project_persona(kiro_dir)
        if has_custom_crews(kiro_dir):
            print(f"Syncing steering only -> {proj} (custom crews, skipping crew sync)")
            sync_steering_to_project(kiro_dir, root)
            generate_vocabulary(kiro_dir, dry_run)
            sync_prompts_to_project(kiro_dir, root)
            generate_project_md_skeleton(kiro_dir)
        else:
            # Determine which crews this project gets
            proj_cfg = fleet.get("projects", {}).get(proj, {}) if fleet else {}
            proj_crews = proj_cfg.get("crews") or fleet.get("defaults", {}).get("crews", None)

            print(f"Syncing crews+steering -> {proj}")

            dest_crews = kiro_dir / "crews"
            dest_crews.mkdir(parents=True, exist_ok=True)

            # Remove old themed crew files
            _stale_crews = [
                "raid-party.yaml", "bug-hunt.yaml", "deploy-squad.yaml",
                "lore-guild.yaml", "recon-squad.yaml", "pit-crew.yaml",
                "content-crew.yaml", "scriptorium.yaml",
            ]
            for stale in _stale_crews:
                stale_path = dest_crews / stale
                if stale_path.exists():
                    stale_path.unlink()

            # Sync only listed crews (or all if no crews: field)
            if proj_crews:
                # Remove base crews not in the list (but keep extends: files)
                all_base = {f.stem for f in base_crews.glob("*.yaml")}
                for existing in dest_crews.glob("*.yaml"):
                    if existing.stem in all_base and existing.stem not in proj_crews:
                        with open(existing, encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        if data and data.get("extends"):
                            continue
                        existing.unlink()
                # Copy only listed crews (skip if local has extends:)
                for crew_name in proj_crews:
                    dest = dest_crews / f"{crew_name}.yaml"
                    if dest.exists():
                        with open(dest, encoding="utf-8") as f:
                            local_data = yaml.safe_load(f)
                        if local_data and local_data.get("extends"):
                            continue
                    src = base_crews / f"{crew_name}.yaml"
                    if src.exists():
                        shutil.copy2(src, dest)
            else:
                for f in base_crews.glob("*.yaml"):
                    shutil.copy2(f, dest_crews / f.name)

            # Sync steering based on persona
            sync_steering_to_project(kiro_dir, root)
            generate_vocabulary(kiro_dir, dry_run)
            sync_prompts_to_project(kiro_dir, root)
            generate_project_md_skeleton(kiro_dir)

    # Generate base crews (from base/crews/*.yaml)
    base_crews_dir = root / "base" / "crews"
    base_output = root / "base" / "agents"
    print(f"\nGenerating: base/crews/*.yaml")
    if not dry_run:
        if base_output.exists():
            shutil.rmtree(base_output)
        base_output.mkdir(parents=True, exist_ok=True)
    base_crew_files = sorted(base_crews_dir.glob("*.yaml"))
    base_siblings = build_sibling_map(base_crew_files)
    agents = []
    for cf in base_crew_files:
        agents.extend(generate(cf, base_output, dry_run, sibling_crews=base_siblings))
    print(f"  -> {len(agents)} agents")

    # Generate each project (projects/ and examples/)
    all_crew_files = sorted(list(examples.glob("*/.kiro/crew.yaml")) + list((root / "examples").glob("*/.kiro/crew.yaml")))
    for crew_file in all_crew_files:
        print(f"\nGenerating: {crew_file}")
        kiro_dir = crew_file.parent
        proj = kiro_dir.parent.name
        crews_dir = kiro_dir / "crews"
        full_mode = crews_dir.is_dir() and any(crews_dir.glob("*.yaml"))
        output_dir = kiro_dir / "agents"
        if not dry_run:
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        agents = []
        if full_mode:
            proj_crew_files = sorted(crews_dir.glob("*.yaml"))
            proj_siblings = build_sibling_map(proj_crew_files)
            for cf in proj_crew_files:
                agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))
        else:
            agents.extend(generate(crew_file, output_dir, dry_run))
            for sibling in sorted(f for f in kiro_dir.glob("*.yaml") if f != crew_file and f.stem != "crew"):
                agents.extend(generate(sibling, output_dir, dry_run))

        print(f"  -> {len(agents)} agents")

        # Apply theme overlay if configured
        proj_cfg = fleet.get("projects", {}).get(proj, {}) if fleet else {}
        theme_name = proj_cfg.get("theme") or fleet.get("defaults", {}).get("theme")
        if theme_name and not dry_run:
            theme = load_theme(theme_name)
            if theme:
                apply_theme_to_agents(output_dir, theme)
                print(f"    + theme: {theme_name}")

        # Generate crew-sheet prompt
        if full_mode and not dry_run:
            theme_for_sheet = load_theme(theme_name) if theme_name else None
            crew_sheet = generate_crew_sheet(crews_dir, theme_for_sheet)
            prompts_dir = kiro_dir / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            (prompts_dir / "crew-sheet.md").write_text(crew_sheet, encoding="utf-8")

        # Generate component steering + subagents if fleet.yaml has this project
        if fleet and proj in fleet.get("projects", {}):
            generate_components_for_project(proj, kiro_dir, fleet, dry_run)

        # Write provenance marker
        if not dry_run:
            import datetime
            shared_prompts_dir = root / "shared" / "prompts"
            meta = {
                "source": "agent-crews",
                "project": proj,
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "agents": agents,
                "shared_prompts": sorted(f.name for f in shared_prompts_dir.glob("*.md")) if shared_prompts_dir.is_dir() else [],
            }
            meta_path = kiro_dir / ".agent-crews-meta.json"
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)
                f.write("\n")

    # Validate coverage gaps
    if fleet:
        validate_coverage(fleet)

    # Generate self-hosted projects (output to repo root .kiro/)
    if fleet:
        for proj_name, proj_cfg in fleet.get("projects", {}).items():
            if not proj_cfg.get("self_hosted"):
                continue
            print(f"\nGenerating self-hosted: {proj_name}")
            kiro_dir = root / ".kiro"
            crews_dir = kiro_dir / "crews"
            output_dir = kiro_dir / "agents"

            # Ensure crews are synced
            proj_crews = proj_cfg.get("crews", [])
            crews_dir.mkdir(parents=True, exist_ok=True)
            for crew_name in proj_crews:
                src = base_crews / f"{crew_name}.yaml"
                if src.exists():
                    shutil.copy2(src, crews_dir / src.name)

            if not dry_run:
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

            # Generate from synced crews
            proj_crew_files = sorted(crews_dir.glob("*.yaml"))
            proj_siblings = build_sibling_map(proj_crew_files)
            agents = []
            for cf in proj_crew_files:
                agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))
            print(f"  -> {len(agents)} agents")

            # Generate crew-sheet
            if not dry_run:
                crew_sheet = generate_crew_sheet(crews_dir)
                prompts_dir = kiro_dir / "prompts"
                prompts_dir.mkdir(parents=True, exist_ok=True)
                (prompts_dir / "crew-sheet.md").write_text(crew_sheet, encoding="utf-8")

            # Generate components
            if fleet and proj_name in fleet.get("projects", {}):
                generate_components_for_project(proj_name, kiro_dir, fleet, dry_run)

    print("\nDone.")


## ─── Theme Overlay System ──────────────────────────────────────────────────────


THEMES_DIR = Path(__file__).parent / "shared" / "themes"


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
    # Build reverse map for prompt substitution (generic → themed)
    name_map = {generic: cfg["name"] for generic, cfg in agent_map.items() if "name" in cfg}

    # Rename all agent files and update contents
    for json_file in sorted(agents_dir.glob("*.json")):
        generic_name = json_file.stem
        if generic_name not in name_map:
            continue

        with open(json_file, encoding="utf-8") as f:
            agent = json.load(f)

        themed_name = name_map[generic_name]
        theme_cfg = agent_map[generic_name]

        # Rename the agent
        agent["name"] = themed_name

        # Replace welcome message if theme provides one
        if "welcomeMessage" in theme_cfg:
            agent["welcomeMessage"] = theme_cfg["welcomeMessage"]

        # Update description: replace [Crew Name] with themed crew display
        crew_display = _get_crew_display_for_agent(generic_name, theme)
        if crew_display and "description" in agent:
            # Replace the [Generic] prefix with themed display
            import re
            agent["description"] = re.sub(
                r"^\[[\w\s-]+\]",
                f"[{crew_display}]",
                agent["description"],
            )

        # Substitute all generic agent names in prompt text with themed names
        if "prompt" in agent:
            agent["prompt"] = _substitute_names_in_text(agent["prompt"], name_map)

        # Update toolsSettings.subagent references
        if "toolsSettings" in agent and "subagent" in agent.get("toolsSettings", {}):
            sub_settings = agent["toolsSettings"]["subagent"]
            for key in ("availableAgents", "trustedAgents"):
                if key in sub_settings:
                    sub_settings[key] = [name_map.get(n, n) for n in sub_settings[key]]

        # Write with new name
        new_path = agents_dir / f"{themed_name}.json"
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(agent, f, indent=2)
            f.write("\n")

        # Remove old file if name changed
        if json_file.name != new_path.name and json_file.exists():
            json_file.unlink()


def _get_crew_display_for_agent(generic_name: str, theme: dict) -> str:
    """Find the themed crew display name for a given generic agent."""
    crews = theme.get("crews", {})
    # Map agent prefixes to crew names
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
    import re
    # Sort by length descending to avoid partial matches
    for generic, themed in sorted(name_map.items(), key=lambda x: -len(x[0])):
        # Replace as whole words (word boundary or preceded by space/slash/backtick)
        text = re.sub(r'(?<![a-zA-Z-])' + re.escape(generic) + r'(?![a-zA-Z-])', themed, text)
    return text


def generate_routing_table(crews_dir: Path) -> str:
    """Auto-generate routing table from agents' routes: fields."""
    lines = ["## Routing Table", "",
             "| Agent | Crew | Routes (send work when...) |",
             "|-------|------|---------------------------|"]
    for crew_file in sorted(crews_dir.glob("*.yaml")):
        with open(crew_file, encoding="utf-8") as f:
            crew = yaml.safe_load(f)
        crew_name = crew.get("workflow", crew_file.stem)
        for archetype in crew.get("architypes", []):
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

        # Apply theme to crew display name
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

        for archetype in crew.get("architypes", []):
            for agent in archetype.get("agents", []):
                generic_name = agent["name"]
                display_name = name_map.get(generic_name, generic_name)
                desc = agent.get("description", "")
                # Strip the [Crew] prefix from description for the table
                import re
                role = re.sub(r"^\[[\w\s-]+\]\s*", "", desc)
                shortcut = agent.get("keyboardShortcut", "")
                cmd = f"`/agent {display_name}`"
                if shortcut:
                    cmd += f" or `{shortcut}`"
                lines.append(f"| {display_name} | {role} | {cmd} |")
        lines.append("")

    return "\n".join(lines) + "\n"


## ─── Component System (Phase 2) ───────────────────────────────────────────────


COMPONENTS_DIR = Path(__file__).parent / "shared" / "components"


def load_fleet_config() -> dict:
    """Load fleet config: fleet.example.yaml (committed) + fleet.yaml (local, overrides)."""
    root = Path(__file__).parent
    fleet = {}

    # Read committed example fleet first (always available)
    example_path = root / "fleet.example.yaml"
    if example_path.exists():
        with open(example_path, encoding="utf-8") as f:
            fleet = yaml.safe_load(f) or {}

    # Read local fleet (overrides example entries)
    local_path = root / "fleet.yaml"
    if local_path.exists():
        with open(local_path, encoding="utf-8") as f:
            local = yaml.safe_load(f) or {}
        if local:
            # Merge: local defaults override example defaults
            if "defaults" in local:
                fleet["defaults"] = deep_merge(fleet.get("defaults", {}), local["defaults"])
            # Merge projects: local entries override same-name entries, but example-only entries persist
            if "projects" in local:
                example_projects = fleet.get("projects", {})
                example_projects.update(local["projects"])
                fleet["projects"] = example_projects

    return fleet


def resolve_component_config(project_name: str, fleet: dict) -> dict:
    """Resolve component config: fleet defaults → project overrides."""
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
    import re

    def _resolve(match):
        key_path = match.group(1)
        # First try flat key lookup (e.g. "notifications.channels" as literal key)
        if key_path in config:
            val = config[key_path]
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            return str(val) if val is not None else ""
        # Fall back to nested dict traversal
        parts = key_path.split(".")
        val = config
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return match.group(0)  # leave unresolved
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
        # Build nested config for placeholder substitution:
        # - Full component_config as nested dict (for cross-component refs like {{notifications.channels}})
        # - Component-specific config merged at top level (for {{channels}}, {{policy}})
        nested = dict(component_config)
        if isinstance(cfg, dict):
            for k, v in cfg.items():
                nested[k] = v

        # Substitute in steering
        if comp.get("steering"):
            comp["steering"] = substitute_placeholders(comp["steering"], nested)
        # Substitute in allowed_commands
        if comp.get("allowed_commands"):
            comp["allowed_commands"] = [
                substitute_placeholders(c, nested) for c in comp["allowed_commands"]
            ]
        components.append(comp)
    return components


def write_steering_files(components: list[dict], kiro_dir: Path):
    """Write .kiro/steering/{universal,orchestrator,worker}/<component>.md from component steering fields."""
    # Map targets to steering subdirectories
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
        name = comp.get("name", "unknown").split("-")[0]  # e.g. "signaling-standard" → "signaling"

        for target in targets:
            subdir = target_dirs.get(target)
            if not subdir:
                continue
            if target == "all":
                # Write to universal
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
            # Subagents intentionally get NO steering resources (fresh context)

            out_path = agents_dir / f"{sub['name']}.json"
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
            # Resolve source relative to component YAML's directory
            comp_name = comp.get("name", "unknown")
            # Derive component dir from name: "notifications-channels" → "notifications"
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
        if subagents:
            print(f"    + subagents: {', '.join(subagents)}")
        if deployed_scripts:
            print(f"    + scripts: {len(deployed_scripts)}")
    else:
        print(f"    Would write steering files for {len(components)} components")


## ─── End Component System ─────────────────────────────────────────────────────


def sync_steering():
    """Copy shared/steering/ to ALL projects based on persona."""
    root = Path(__file__).parent
    examples = root / "projects"

    print("Syncing steering to all projects (persona-aware)...")

    for kiro_dir in sorted(examples.glob("*/.kiro")):
        proj = kiro_dir.parent.name
        persona = get_project_persona(kiro_dir)
        sync_steering_to_project(kiro_dir, root)
        print(f"  {proj}: persona={persona}")

    print("Done.")


def sync_prompts():
    """Copy shared/prompts/ to ALL projects."""
    root = Path(__file__).parent
    examples = root / "projects"

    print("Syncing shared prompts to all projects...")

    for kiro_dir in sorted(examples.glob("*/.kiro")):
        proj = kiro_dir.parent.name
        sync_prompts_to_project(kiro_dir, root)
        print(f"  {proj}")

    print("Done.")


def check_health():
    """Validate allowedCommands vs project.md DO NOTs for each project."""
    import re
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    root = Path(__file__).parent
    examples = root / "projects"

    print("Checking health across projects...")

    for proj_dir in sorted(examples.iterdir()):
        if not proj_dir.is_dir():
            continue
        kiro_dir = proj_dir / ".kiro"
        if not kiro_dir.is_dir():
            continue
        proj = proj_dir.name

        # Collect allowedCommands from crew.yaml and crews/*.yaml
        allowed = []
        yaml_files = list(kiro_dir.glob("crew.yaml")) + list(kiro_dir.glob("crews/*.yaml"))
        for yf in yaml_files:
            with open(yf, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            # Walk the yaml looking for allowedCommands lists
            _collect_allowed(data, allowed)

        # Read project.md DO NOT section
        project_md = kiro_dir / "steering" / "project.md"
        if not project_md.exists():
            print(f"  ✅ {proj}: no project.md")
            continue

        donot_lines = _extract_donot_section(project_md)
        if not donot_lines:
            print(f"  ✅ {proj}: no contradictions")
            continue

        # Check for contradictions
        warnings = []
        for line in donot_lines:
            line_lower = line.lower()
            for cmd in allowed:
                # Strip glob suffix for matching
                cmd_base = cmd.rstrip(" *").lower()
                # Skip short commands (<=3 chars) unless they appear as a command reference
                if len(cmd_base) <= 3:
                    # Only match if preceded by "run " or backtick or start-of-word boundary
                    import re
                    if not re.search(r'(?:run\s+|`|^\s*-\s*)' + re.escape(cmd_base) + r'(?:\s|`|$)', line_lower):
                        continue
                if cmd_base and cmd_base in line_lower:
                    warnings.append((cmd, line.strip()))
                    break

        if warnings:
            for cmd, donot_line in warnings:
                print(f"  ⚠️  {proj}: allowedCommands permits '{cmd.rstrip(' *')}' but project.md says '{donot_line}'")
        else:
            print(f"  ✅ {proj}: no contradictions")


def _collect_allowed(obj, allowed):
    """Recursively find all allowedCommands values in a yaml structure."""
    if isinstance(obj, dict):
        if "allowedCommands" in obj and isinstance(obj["allowedCommands"], list):
            allowed.extend(obj["allowedCommands"])
        for v in obj.values():
            _collect_allowed(v, allowed)
    elif isinstance(obj, list):
        for item in obj:
            _collect_allowed(item, allowed)


def _extract_donot_section(project_md: Path) -> list[str]:
    """Extract lines from the ## DO NOT section of project.md."""
    lines = project_md.read_text(encoding="utf-8").splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.strip().lower().startswith("## do not"):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            if line.strip():
                result.append(line)
    # Also grab individual "NEVER" / "Do not run" lines outside a dedicated section
    if not result:
        for line in lines:
            if any(kw in line.lower() for kw in ["never run", "do not run", "don't run"]):
                result.append(line)
    return result


def main():
    dry_run = "--dry-run" in sys.argv
    append = "--append" in sys.argv
    all_flag = "--all" in sys.argv
    sync_steering_flag = "--sync-steering" in sys.argv
    sync_prompts_flag = "--sync-prompts" in sys.argv
    check_health_flag = "--check-health" in sys.argv
    components_flag = "--components" in sys.argv
    args = [a for a in sys.argv[1:] if a not in ("--dry-run", "--append", "--all", "--sync-steering", "--sync-prompts", "--check-health", "--components")]

    if sync_steering_flag:
        sync_steering()
        return

    if sync_prompts_flag:
        sync_prompts()
        return

    if check_health_flag:
        check_health()
        return

    if components_flag:
        # Generate component steering + subagents for all fleet projects
        fleet = load_fleet_config()
        if not fleet:
            sys.exit("No fleet.yaml found")
        root = Path(__file__).parent
        for proj_name, proj_cfg in fleet.get("projects", {}).items():
            if proj_cfg.get("deploy") is False:
                continue
            kiro_dir = root / "projects" / proj_name / ".kiro"
            if not kiro_dir.exists():
                continue
            print(f"Components: {proj_name}")
            generate_components_for_project(proj_name, kiro_dir, fleet, dry_run)
        print("Done.")
        return

    if all_flag:
        generate_all(dry_run)
        return

    crew_path = Path(args[0]) if args else Path(".kiro/crew.yaml")
    if not crew_path.exists():
        sys.exit(f"Not found: {crew_path}")

    # Output dir is always agents/ next to the crew.yaml (or its parent .kiro/)
    if crew_path.parent.name == ".kiro":
        output_dir = crew_path.parent / "agents"
    else:
        output_dir = crew_path.parent / "agents"

    if not dry_run:
        if output_dir.exists() and not append:
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Determine mode: if crews/ exists, use full mode (skip basic crew.yaml)
    crews_dir = crew_path.parent / "crews"
    full_mode = crews_dir.is_dir() and any(crews_dir.glob("*.yaml"))

    # Auto-detect sibling crew yamls in the same directory
    sibling_yamls = sorted(
        f for f in crew_path.parent.glob("*.yaml")
        if f != crew_path and f.stem != "crew"
    )

    agents = []

    if full_mode:
        # Full mode: only generate from crews/*.yaml
        for crew_file in sorted(crews_dir.glob("*.yaml")):
            print(f"Generating from: {crew_file}")
            extra = generate(crew_file, output_dir, dry_run)
            agents.extend(extra)
    else:
        # Basic mode: generate from crew.yaml + any sibling yamls
        print(f"Generating from: {crew_path}")
        agents = generate(crew_path, output_dir, dry_run)
        for sibling in sibling_yamls:
            print(f"Generating from: {sibling}")
            extra = generate(sibling, output_dir, dry_run)
            agents.extend(extra)

    print(f"Generated {len(agents)} agents: {', '.join(agents)}")

    if not dry_run:
        print(f"Output: {output_dir}/")


if __name__ == "__main__":
    main()
