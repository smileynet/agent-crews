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
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")


from _lib import get_architypes, deep_merge
from _lib.validate import validate_coverage, validate_changelog_prerequisites, validate_hierarchy
from _lib.theme import load_theme, apply_theme_to_agents
from _lib.sync import sync_steering_to_project, sync_skills_to_project, sync_prompts_to_project, get_project_persona
from _lib.utils import (
    has_custom_crews, generate_project_md_skeleton, build_sibling_map,
    collect_shared_agents, generate_routing_table, generate_crew_sheet,
)
from _lib.components import (
    resolve_component_config, load_component, load_all_components,
    write_steering_files, generate_subagents, deploy_scripts,
    write_scripts_steering, inject_subagents_into_orchestrators,
    substitute_placeholders, generate_components_for_project,
)
from _lib.build import build_agent, resolve_extends, generate


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
        if has_custom_crews(kiro_dir):
            print(f"Syncing steering only -> {proj} (custom crews, skipping crew sync)")
            sync_steering_to_project(kiro_dir, root)
            sync_skills_to_project(kiro_dir, root)
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
            sync_skills_to_project(kiro_dir, root)
            sync_prompts_to_project(kiro_dir, root)
            generate_project_md_skeleton(kiro_dir)

    # Generate base crews (from base/crews/*.yaml)
    base_crews_dir = root / "base" / "crews"
    base_output = root / "base" / "agents"
    print("\nGenerating: base/crews/*.yaml")
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

        # Synthesize dispatcher + shared agents + components
        if not dry_run:
            crew_sources = sorted(crews_dir.glob("*.yaml")) if full_mode else [crew_file]
            shared_names = collect_shared_agents(crew_sources)
            synthesize_dispatcher(crew_sources, shared_names, kiro_dir, dry_run=dry_run)

        # Generate component steering + subagents if fleet.yaml has this project
        if fleet and proj in fleet.get("projects", {}):
            generate_components_for_project(proj, kiro_dir, fleet, dry_run)

        # Inject shared agents into all orchestrators (including dispatcher)
        if not dry_run and shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)

        # Write provenance marker
        if not dry_run:
            shared_prompts_dir = root / "shared" / "prompts"
            meta = {
                "source": "agent-crews",
                "project": proj,
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
        validate_changelog_prerequisites(fleet)

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

            # Synthesize dispatcher + shared agents + components
            if not dry_run:
                shared_names = collect_shared_agents(proj_crew_files)
                dispatcher_cfg = proj_cfg.get("dispatcher", {})
                synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)

            # Generate components (after dispatcher so injection covers it)
            if fleet and proj_name in fleet.get("projects", {}):
                generate_components_for_project(proj_name, kiro_dir, fleet, dry_run)

            # Inject shared agents into all orchestrators (including dispatcher)
            if not dry_run and shared_names:
                inject_subagents_into_orchestrators(shared_names, kiro_dir)

    # --- NEW: Generate from fleet.local.yaml projects with .crews/ ---
    fleet_local = load_fleet_local()
    for proj_name, proj_path in fleet_local.items():
        proj_dir = Path(proj_path).expanduser()
        crews_config = proj_dir / '.crews' / 'crew.yaml'
        if not crews_config.exists():
            continue
        # Skip if already handled above (projects/ dir)
        if (root / 'projects' / proj_name / '.kiro').exists():
            continue
        print(f"\nGenerating (in-place): {proj_name}")
        kiro_dir = proj_dir / '.kiro'
        # Remove dangling symlink from old deployment model
        if kiro_dir.is_symlink() and not kiro_dir.exists():
            kiro_dir.unlink()
        # Read crew config to get crews list
        with open(crews_config, encoding='utf-8') as f:
            crew_cfg = yaml.safe_load(f) or {}
        proj_crews = crew_cfg.get('crews', ['general'])
        # Sync base crews to a temp crews dir inside .kiro
        crews_dir = kiro_dir / 'crews'
        crews_dir.mkdir(parents=True, exist_ok=True)
        for crew_name in proj_crews:
            src = base_crews / f"{crew_name}.yaml"
            if src.exists():
                shutil.copy2(src, crews_dir / src.name)
        # Generate agents
        output_dir = kiro_dir / 'agents'
        if not dry_run:
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        proj_crew_files = sorted(crews_dir.glob('*.yaml'))
        proj_siblings = build_sibling_map(proj_crew_files)
        agents = []
        for cf in proj_crew_files:
            agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))
        print(f"  -> {len(agents)} agents")
        # Apply theme
        theme_name = crew_cfg.get('theme')
        if theme_name and not dry_run:
            theme = load_theme(theme_name)
            if theme:
                apply_theme_to_agents(output_dir, theme)
        # Generate crew-sheet
        if not dry_run:
            theme_for_sheet = load_theme(theme_name) if theme_name else None
            crew_sheet = generate_crew_sheet(crews_dir, theme_for_sheet)
            prompts_dir = kiro_dir / 'prompts'
            prompts_dir.mkdir(parents=True, exist_ok=True)
            (prompts_dir / 'crew-sheet.md').write_text(crew_sheet, encoding='utf-8')
        # Sync steering
        sync_steering_to_project(kiro_dir, root)
        sync_skills_to_project(kiro_dir, root)
        sync_prompts_to_project(kiro_dir, root)
        generate_project_md_skeleton(kiro_dir)
        # Synthesize dispatcher
        if not dry_run:
            shared_names = collect_shared_agents(proj_crew_files)
            dispatcher_cfg = crew_cfg.get("dispatcher", {})
            synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)
        # Components (after dispatcher so injection covers it)
        if fleet:
            # Build a synthetic fleet entry from .crews/crew.yaml
            synthetic_fleet = {'projects': {proj_name: crew_cfg}, 'defaults': fleet.get('defaults', {})}
            generate_components_for_project(proj_name, kiro_dir, synthetic_fleet, dry_run)
        # Inject shared agents into all orchestrators (including dispatcher)
        if not dry_run and shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)
        # Clean up: remove .kiro/crews/ (was only needed for generation)
        if not dry_run:
            crews_cleanup = kiro_dir / 'crews'
            if crews_cleanup.is_dir():
                shutil.rmtree(crews_cleanup)

    print("\nDone.")


## ─── Theme Overlay System ──────────────────────────────────────────────────────





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


def load_fleet_local() -> dict:
    """Load fleet.local.yaml (name→path project registry)."""
    root = Path(__file__).parent
    path = root / "fleet.local.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("projects", {})


def resolve_project(name_or_path: str) -> Path:
    """Resolve project name or '.' to the project root directory."""
    if name_or_path == '.':
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / '.crews' / 'crew.yaml').exists():
                return cwd
            cwd = cwd.parent
        sys.exit('No .crews/crew.yaml found in cwd or parents')
    # Check if it's a path
    p = Path(name_or_path).expanduser()
    if p.is_dir() and (p / '.crews' / 'crew.yaml').exists():
        return p
    # Look up in fleet.local.yaml
    fleet = load_fleet_local()
    if name_or_path in fleet:
        resolved = Path(fleet[name_or_path]).expanduser()
        if (resolved / '.crews' / 'crew.yaml').exists():
            return resolved
        # Fallback: maybe it still uses old .kiro/crew.yaml layout
        if (resolved / '.kiro' / 'crew.yaml').exists():
            return resolved
    sys.exit(f'Project not found or missing .crews/crew.yaml: {name_or_path}')



def synthesize_dispatcher(
    crew_files: list[Path],
    shared_agents: list[str],
    kiro_dir: Path,
    dispatcher_config: dict = None,
    dry_run: bool = False,
) -> str:
    """Auto-generate a project dispatcher from crew composition (ADR-008)."""
    dispatcher_config = dispatcher_config or {}

    # Collect leads (type: orchestrator agents) from all crews
    leads = []
    for cf in crew_files:
        try:
            crew = yaml.safe_load(cf.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        for archetype in get_architypes(crew or {}):
            if archetype.get("type") != "orchestrator":
                continue
            for agent in archetype.get("agents", []):
                leads.append({
                    "name": agent["name"],
                    "description": agent.get("description", ""),
                    "routes": agent.get("routes", ""),
                })

    if not leads:
        return ""

    # Build routing table
    routing_lines = ["| Crew Lead | Send work when... |",
                     "|-----------|-------------------|"]
    for lead in leads:
        routing_lines.append(f"| {lead['name']} | {lead['routes']} |")
    routing_table = "\n".join(routing_lines)

    # Build shared utilities section (with routing hints)
    if shared_agents:
        shared_lines_parts = []
        for name in shared_agents:
            # Find the agent's routes or description from crew files
            routes_hint = ""
            for cf in crew_files:
                try:
                    crew_data = yaml.safe_load(cf.read_text(encoding="utf-8"))
                except (yaml.YAMLError, OSError):
                    continue
                for arch in get_architypes(crew_data or {}):
                    for ag in arch.get("agents", []):
                        if ag["name"] == name and ag.get("routes"):
                            routes_hint = ag["routes"]
                            break
            if routes_hint:
                shared_lines_parts.append(f"- {name} → {routes_hint}")
            else:
                shared_lines_parts.append(f"- {name}")
        shared_lines = "\n".join(shared_lines_parts)
    else:
        shared_lines = "(none configured)"

    # Build prompt
    prompt_suffix = dispatcher_config.get("prompt_suffix", "")
    prompt = f"""You are dispatcher — the project orchestrator.

## Routing Principle

Route based on INTENT, not completeness. If you know which lead handles it, delegate immediately — even if details are missing. Workers gather their own details. Only ask when you genuinely cannot determine which lead to route to.

Do NOT ask clarifying questions about task details (what kind of agent, which file, etc.) — delegate with whatever context the user provided and let the specialist ask if needed.

## Routing Decision (MANDATORY — before ANY tool call)

Classify the request FIRST. Do not read files to "understand" the request before routing.

| Request type | Action |
|-------------|--------|
| Simple read (list a directory, show a known file) | Self-execute with read tool |
| Needs investigation, creation, modification, or diagnosis | DELEGATE to crew lead |
| Cannot determine which lead handles this | Ask one clarifying question |

You have only: read, subagent, todo_list. You CANNOT write, execute commands, search, or grep.
Any task requiring those capabilities MUST be delegated.

## Routing Table

{routing_table}

## Shared Utilities
Dispatch directly (no lead needed) for one-shot tasks:
{shared_lines}

Route to these when the request matches their domain — don't attempt the work yourself.

## Delegation Format
Always include:
- agentName: exact agent name
- task: clear description of what to achieve
- context: relevant details from user request

## Rules
- Simple read (file you know the path to) → answer directly
- Everything else → DELEGATE to the appropriate crew lead
- Multi-crew work → plan the sequence with todo_list, dispatch leads in order
- Never investigate a problem yourself — you lack the tools for it
- Always narrate: "Delegating to X because Y"
- When in doubt → DELEGATE (false delegation is cheap, false self-execution fails)
{prompt_suffix}"""

    # Build welcome message
    welcome_lines = ["🎯 Dispatcher ready. What are we working on?\n",
                     "Available crews:"]
    for lead in leads:
        short_desc = lead["routes"][:60] if lead["routes"] else lead["description"][:60]
        welcome_lines.append(f"- {short_desc} → {lead['name']}")
    welcome_lines.append("")
    if shared_agents:
        welcome_lines.append(f"Utilities: {', '.join(shared_agents)}")
        welcome_lines.append("")
    welcome_lines.append("Or just tell me what to do — simple tasks I'll handle directly.")
    welcome_message = "\n".join(welcome_lines)

    # Build available agents list (leads + shared agents)
    available = [lead["name"] for lead in leads] + shared_agents
    shortcut = dispatcher_config.get("keyboard_shortcut", "ctrl+shift+d")

    agent_json = {
        "name": "dispatcher",
        "description": "Project orchestrator — plans work, routes to crew leads, reads context",
        "tools": ["read", "subagent", "todo_list"],
        "allowedTools": ["read", "subagent", "todo_list"],
        "toolsSettings": {
            "subagent": {
                "availableAgents": available,
                "trustedAgents": available,
            },
        },
        "prompt": prompt,
        "welcomeMessage": welcome_message,
        "keyboardShortcut": shortcut,
    }

    # Add resources
    resources = []
    agents_md = kiro_dir.parent / "AGENTS.md"
    if agents_md.exists():
        resources.append("file://AGENTS.md")
    if resources:
        agent_json["resources"] = resources

    # Write
    out_path = kiro_dir / "agents" / "dispatcher.json"
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(agent_json, f, indent=2)
            f.write("\n")

    return "dispatcher"


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
    import io
    import re
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

    # Handle project name or '.' argument
    if args and not Path(args[0]).suffix:
        # Looks like a project name or '.', not a file path
        candidate = args[0]
        if candidate == '.' or not Path(candidate).exists():
            try:
                proj_dir = resolve_project(candidate)
                crews_config = proj_dir / '.crews' / 'crew.yaml'
                if crews_config.exists():
                    # Generate in-place for this project
                    print(f"Building: {proj_dir.name}")
                    # Reuse generate_all logic for single project
                    root = Path(__file__).parent
                    base_crews_dir = root / 'base' / 'crews'
                    fleet_cfg = load_fleet_config()
                    with open(crews_config, encoding='utf-8') as f:
                        crew_cfg = yaml.safe_load(f) or {}
                    proj_crews = crew_cfg.get('crews', ['general'])
                    kiro_dir = proj_dir / '.kiro'
                    # Remove dangling symlink from old deployment model
                    if kiro_dir.is_symlink() and not kiro_dir.exists():
                        kiro_dir.unlink()
                    crews_dir = kiro_dir / 'crews'
                    crews_dir.mkdir(parents=True, exist_ok=True)
                    for crew_name in proj_crews:
                        src = base_crews_dir / f"{crew_name}.yaml"
                        if src.exists():
                            shutil.copy2(src, crews_dir / src.name)
                    output_dir = kiro_dir / 'agents'
                    if not dry_run:
                        if output_dir.exists():
                            shutil.rmtree(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                    proj_crew_files = sorted(crews_dir.glob('*.yaml'))
                    proj_siblings = build_sibling_map(proj_crew_files)
                    agents = []
                    for cf in proj_crew_files:
                        agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))
                    print(f"  -> {len(agents)} agents")
                    theme_name = crew_cfg.get('theme')
                    if theme_name and not dry_run:
                        theme = load_theme(theme_name)
                        if theme:
                            apply_theme_to_agents(output_dir, theme)
                    if not dry_run:
                        theme_for_sheet = load_theme(theme_name) if theme_name else None
                        crew_sheet = generate_crew_sheet(crews_dir, theme_for_sheet)
                        prompts_dir = kiro_dir / 'prompts'
                        prompts_dir.mkdir(parents=True, exist_ok=True)
                        (prompts_dir / 'crew-sheet.md').write_text(crew_sheet, encoding='utf-8')
                    sync_steering_to_project(kiro_dir, root)
                    sync_skills_to_project(kiro_dir, root)
                    sync_prompts_to_project(kiro_dir, root)
                    generate_project_md_skeleton(kiro_dir)
                    # Synthesize dispatcher + inject shared agents
                    if not dry_run:
                        shared_names = collect_shared_agents(proj_crew_files)
                        dispatcher_cfg = crew_cfg.get("dispatcher", {})
                        synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)
                    # Components (runs after dispatcher so injection covers it)
                    if fleet_cfg or crew_cfg.get('components'):
                        synthetic = {'projects': {proj_dir.name: crew_cfg}, 'defaults': fleet_cfg.get('defaults', {}) if fleet_cfg else {}}
                        generate_components_for_project(proj_dir.name, kiro_dir, synthetic, dry_run)
                    # Inject shared agents into all orchestrators (including dispatcher)
                    if not dry_run and shared_names:
                        inject_subagents_into_orchestrators(shared_names, kiro_dir)
                    # Clean up: remove .kiro/crews/ (was only needed for generation)
                    if not dry_run:
                        crews_cleanup = kiro_dir / 'crews'
                        if crews_cleanup.is_dir():
                            shutil.rmtree(crews_cleanup)
                    print(f"Generated {len(agents)} agents at {output_dir}/")
                    return
            except SystemExit:
                pass  # Fall through to old behavior

    crew_path = Path(args[0]) if args else Path(".kiro/crew.yaml")
    if not crew_path.exists():
        # Fallback: try resolving as a .crews/ project
        if not args and Path(".crews/crew.yaml").exists():
            try:
                proj_dir = resolve_project(".")
                # Re-enter main logic via the project path
                sys.argv = [sys.argv[0], "."] + (["--dry-run"] if dry_run else [])
                main()
                return
            except SystemExit:
                pass
        sys.exit(f"Not found: {crew_path}")

    # Output dir is always agents/ next to the crew.yaml (or its parent .kiro/)
    output_dir = crew_path.parent / "agents" if crew_path.parent.name == ".kiro" else crew_path.parent / "agents"

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

    # Synthesize dispatcher + inject shared agents
    if not dry_run:
        kiro_dir = output_dir.parent
        crew_sources = sorted(crews_dir.glob("*.yaml")) if full_mode else ([crew_path] + sibling_yamls)
        shared_names = collect_shared_agents(crew_sources)
        synthesize_dispatcher(crew_sources, shared_names, kiro_dir, dry_run=dry_run)
        if shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)

    if not dry_run:
        print(f"Output: {output_dir}/")


if __name__ == "__main__":
    main()
