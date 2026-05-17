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

import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml required: pip install pyyaml")

from _lib.build import generate
from _lib.components import generate_components_for_project, inject_subagents_into_orchestrators
from _lib.fleet import (
    check_health, generate_all, load_fleet_config, resolve_project,
    sync_prompts, sync_steering,
)
from _lib.inject import synthesize_dispatcher
from _lib.sync import sync_prompts_to_project, sync_skills_to_project, sync_steering_to_project
from _lib.theme import apply_theme_to_agents, load_theme
from _lib.utils import (
    build_sibling_map, collect_shared_agents, generate_crew_sheet,
    generate_project_md_skeleton,
)


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
        candidate = args[0]
        if candidate == '.' or not Path(candidate).exists():
            try:
                proj_dir = resolve_project(candidate)
                crews_config = proj_dir / '.crews' / 'crew.yaml'
                if crews_config.exists():
                    print(f"Building: {proj_dir.name}")
                    root = Path(__file__).parent
                    base_crews_dir = root / 'base' / 'crews'
                    fleet_cfg = load_fleet_config()
                    with open(crews_config, encoding='utf-8') as f:
                        crew_cfg = yaml.safe_load(f) or {}
                    proj_crews = crew_cfg.get('crews', ['general'])
                    kiro_dir = proj_dir / '.kiro'
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
                    if not dry_run:
                        shared_names = collect_shared_agents(proj_crew_files)
                        dispatcher_cfg = crew_cfg.get("dispatcher", {})
                        synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)
                    if fleet_cfg or crew_cfg.get('components'):
                        synthetic = {'projects': {proj_dir.name: crew_cfg}, 'defaults': fleet_cfg.get('defaults', {}) if fleet_cfg else {}}
                        generate_components_for_project(proj_dir.name, kiro_dir, synthetic, dry_run)
                    if not dry_run and shared_names:
                        inject_subagents_into_orchestrators(shared_names, kiro_dir)
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
        if not args and Path(".crews/crew.yaml").exists():
            try:
                resolve_project(".")
                sys.argv = [sys.argv[0], "."] + (["--dry-run"] if dry_run else [])
                main()
                return
            except SystemExit:
                pass
        sys.exit(f"Not found: {crew_path}")

    output_dir = crew_path.parent / "agents"

    if not dry_run:
        if output_dir.exists() and not append:
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    crews_dir = crew_path.parent / "crews"
    full_mode = crews_dir.is_dir() and any(crews_dir.glob("*.yaml"))

    sibling_yamls = sorted(
        f for f in crew_path.parent.glob("*.yaml")
        if f != crew_path and f.stem != "crew"
    )

    agents = []

    if full_mode:
        for crew_file in sorted(crews_dir.glob("*.yaml")):
            print(f"Generating from: {crew_file}")
            extra = generate(crew_file, output_dir, dry_run)
            agents.extend(extra)
    else:
        print(f"Generating from: {crew_path}")
        agents = generate(crew_path, output_dir, dry_run)
        for sibling in sibling_yamls:
            print(f"Generating from: {sibling}")
            extra = generate(sibling, output_dir, dry_run)
            agents.extend(extra)

    print(f"Generated {len(agents)} agents: {', '.join(agents)}")

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
