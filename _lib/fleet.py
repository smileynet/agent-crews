"""Fleet orchestration: generate all projects, load config, health checks."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import yaml

from _lib import deep_merge
from _lib.build import generate
from _lib.components import generate_components_for_project, inject_subagents_into_orchestrators
from _lib.inject import synthesize_dispatcher
from _lib.sync import get_project_persona, sync_prompts_to_project, sync_skills_to_project, sync_steering_to_project
from _lib.theme import apply_theme_to_agents, load_theme
from _lib.utils import (
    build_sibling_map,
    collect_shared_agents,
    generate_crew_sheet,
    generate_project_md_skeleton,
    has_custom_crews,
)
from _lib.validate import validate_changelog_prerequisites, validate_coverage


def generate_all(dry_run: bool = False):
    """Sync crews+steering from base to all projects, then generate all."""
    root = Path(__file__).parent.parent
    base_crews = root / "base" / "crews"
    examples = root / "projects"

    fleet = load_fleet_config()

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
            proj_cfg = fleet.get("projects", {}).get(proj, {}) if fleet else {}
            proj_crews = proj_cfg.get("crews") or fleet.get("defaults", {}).get("crews", None)

            print(f"Syncing crews+steering -> {proj}")

            dest_crews = kiro_dir / "crews"
            dest_crews.mkdir(parents=True, exist_ok=True)

            _stale_crews = [
                "raid-party.yaml", "bug-hunt.yaml", "deploy-squad.yaml",
                "lore-guild.yaml", "recon-squad.yaml", "pit-crew.yaml",
                "content-crew.yaml", "scriptorium.yaml",
            ]
            for stale in _stale_crews:
                stale_path = dest_crews / stale
                if stale_path.exists():
                    stale_path.unlink()

            if proj_crews:
                all_base = {f.stem for f in base_crews.glob("*.yaml")}
                for existing in dest_crews.glob("*.yaml"):
                    if existing.stem in all_base and existing.stem not in proj_crews:
                        with open(existing, encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        if data and data.get("extends"):
                            continue
                        existing.unlink()
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

            sync_steering_to_project(kiro_dir, root)
            sync_skills_to_project(kiro_dir, root)
            sync_prompts_to_project(kiro_dir, root)
            generate_project_md_skeleton(kiro_dir)

    # Generate base crews
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

    # Generate each project
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

        proj_cfg = fleet.get("projects", {}).get(proj, {}) if fleet else {}
        theme_name = proj_cfg.get("theme") or fleet.get("defaults", {}).get("theme")
        if theme_name and not dry_run:
            theme = load_theme(theme_name)
            if theme:
                apply_theme_to_agents(output_dir, theme)
                print(f"    + theme: {theme_name}")

        if full_mode and not dry_run:
            theme_for_sheet = load_theme(theme_name) if theme_name else None
            crew_sheet = generate_crew_sheet(crews_dir, theme_for_sheet)
            prompts_dir = kiro_dir / "prompts"
            prompts_dir.mkdir(parents=True, exist_ok=True)
            (prompts_dir / "crew-sheet.md").write_text(crew_sheet, encoding="utf-8")

        if not dry_run:
            crew_sources = sorted(crews_dir.glob("*.yaml")) if full_mode else [crew_file]
            shared_names = collect_shared_agents(crew_sources)
            synthesize_dispatcher(crew_sources, shared_names, kiro_dir, dry_run=dry_run)

        if fleet and proj in fleet.get("projects", {}):
            generate_components_for_project(proj, kiro_dir, fleet, dry_run)

        if not dry_run and shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)

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

    if fleet:
        validate_coverage(fleet)
        validate_changelog_prerequisites(fleet)

    # Generate self-hosted projects
    if fleet:
        for proj_name, proj_cfg in fleet.get("projects", {}).items():
            if not proj_cfg.get("self_hosted"):
                continue
            print(f"\nGenerating self-hosted: {proj_name}")
            kiro_dir = root / ".kiro"
            crews_dir = kiro_dir / "crews"
            output_dir = kiro_dir / "agents"

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

            proj_crew_files = sorted(crews_dir.glob("*.yaml"))
            proj_siblings = build_sibling_map(proj_crew_files)
            agents = []
            for cf in proj_crew_files:
                agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))
            print(f"  -> {len(agents)} agents")

            if not dry_run:
                crew_sheet = generate_crew_sheet(crews_dir)
                prompts_dir = kiro_dir / "prompts"
                prompts_dir.mkdir(parents=True, exist_ok=True)
                (prompts_dir / "crew-sheet.md").write_text(crew_sheet, encoding="utf-8")

            if not dry_run:
                shared_names = collect_shared_agents(proj_crew_files)
                dispatcher_cfg = proj_cfg.get("dispatcher", {})
                synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)

            if fleet and proj_name in fleet.get("projects", {}):
                generate_components_for_project(proj_name, kiro_dir, fleet, dry_run)

            if not dry_run and shared_names:
                inject_subagents_into_orchestrators(shared_names, kiro_dir)

    # Generate from fleet.local.yaml projects
    fleet_local = load_fleet_local()
    for proj_name, proj_path in fleet_local.items():
        proj_dir = Path(proj_path).expanduser()
        crews_config = proj_dir / '.crews' / 'crew.yaml'
        if not crews_config.exists():
            continue
        if (root / 'projects' / proj_name / '.kiro').exists():
            continue
        print(f"\nGenerating (in-place): {proj_name}")
        kiro_dir = proj_dir / '.kiro'
        if kiro_dir.is_symlink() and not kiro_dir.exists():
            kiro_dir.unlink()
        with open(crews_config, encoding='utf-8') as f:
            crew_cfg = yaml.safe_load(f) or {}
        proj_crews = crew_cfg.get('crews', ['general'])
        crews_dir = kiro_dir / 'crews'
        crews_dir.mkdir(parents=True, exist_ok=True)
        for crew_name in proj_crews:
            src = base_crews / f"{crew_name}.yaml"
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
        if not dry_run:
            shared_names = collect_shared_agents(proj_crew_files)
            dispatcher_cfg = crew_cfg.get("dispatcher", {})
            synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)
        if fleet:
            synthetic_fleet = {'projects': {proj_name: crew_cfg}, 'defaults': fleet.get('defaults', {})}
            generate_components_for_project(proj_name, kiro_dir, synthetic_fleet, dry_run)
        if not dry_run and shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)
        if not dry_run:
            crews_cleanup = kiro_dir / 'crews'
            if crews_cleanup.is_dir():
                shutil.rmtree(crews_cleanup)

    print("\nDone.")


def load_fleet_config() -> dict:
    """Load fleet config: fleet.example.yaml (committed) + fleet.yaml (local, overrides)."""
    root = Path(__file__).parent.parent
    fleet = {}

    example_path = root / "fleet.example.yaml"
    if example_path.exists():
        with open(example_path, encoding="utf-8") as f:
            fleet = yaml.safe_load(f) or {}

    local_path = root / "fleet.yaml"
    if local_path.exists():
        with open(local_path, encoding="utf-8") as f:
            local = yaml.safe_load(f) or {}
        if local:
            if "defaults" in local:
                fleet["defaults"] = deep_merge(fleet.get("defaults", {}), local["defaults"])
            if "projects" in local:
                example_projects = fleet.get("projects", {})
                example_projects.update(local["projects"])
                fleet["projects"] = example_projects

    return fleet


def load_fleet_local() -> dict:
    """Load fleet.local.yaml (name→path project registry)."""
    root = Path(__file__).parent.parent
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
    p = Path(name_or_path).expanduser()
    if p.is_dir() and (p / '.crews' / 'crew.yaml').exists():
        return p
    fleet = load_fleet_local()
    if name_or_path in fleet:
        resolved = Path(fleet[name_or_path]).expanduser()
        if (resolved / '.crews' / 'crew.yaml').exists():
            return resolved
        if (resolved / '.kiro' / 'crew.yaml').exists():
            return resolved
    sys.exit(f'Project not found or missing .crews/crew.yaml: {name_or_path}')


def sync_steering():
    """Copy shared/steering/ to ALL projects based on persona."""
    root = Path(__file__).parent.parent
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
    root = Path(__file__).parent.parent
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
    root = Path(__file__).parent.parent
    examples = root / "projects"

    print("Checking health across projects...")

    for proj_dir in sorted(examples.iterdir()):
        if not proj_dir.is_dir():
            continue
        kiro_dir = proj_dir / ".kiro"
        if not kiro_dir.is_dir():
            continue
        proj = proj_dir.name

        allowed = []
        yaml_files = list(kiro_dir.glob("crew.yaml")) + list(kiro_dir.glob("crews/*.yaml"))
        for yf in yaml_files:
            with open(yf, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue
            _collect_allowed(data, allowed)

        project_md = kiro_dir / "steering" / "project.md"
        if not project_md.exists():
            print(f"  ✅ {proj}: no project.md")
            continue

        donot_lines = _extract_donot_section(project_md)
        if not donot_lines:
            print(f"  ✅ {proj}: no contradictions")
            continue

        warnings = []
        for line in donot_lines:
            line_lower = line.lower()
            for cmd in allowed:
                cmd_base = cmd.rstrip(" *").lower()
                if len(cmd_base) <= 3 and not re.search(r'(?:run\s+|`|^\s*-\s*)' + re.escape(cmd_base) + r'(?:\s|`|$)', line_lower):
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
    if not result:
        for line in lines:
            if any(kw in line.lower() for kw in ["never run", "do not run", "don't run"]):
                result.append(line)
    return result
