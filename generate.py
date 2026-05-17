#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Generate .kiro/agents/*.json from a crew.yaml file.

Usage:
    uv run generate.py                    # reads .crews/crew.yaml or .kiro/crew.yaml
    uv run generate.py <project>          # build a named project or '.'
    uv run generate.py path/to/crew.yaml  # custom input
    uv run generate.py --dry-run          # print what would be written
    uv run generate.py --all              # generate all projects
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
    build_single_project,
    check_health,
    generate_all,
    load_fleet_config,
    resolve_project,
    sync_prompts,
    sync_steering,
)
from _lib.inject import synthesize_dispatcher
from _lib.utils import collect_shared_agents


def main():
    dry_run = "--dry-run" in sys.argv
    append = "--append" in sys.argv
    all_flag = "--all" in sys.argv
    sync_steering_flag = "--sync-steering" in sys.argv
    sync_prompts_flag = "--sync-prompts" in sys.argv
    check_health_flag = "--check-health" in sys.argv
    components_flag = "--components" in sys.argv
    args = [a for a in sys.argv[1:] if a not in (
        "--dry-run", "--append", "--all", "--sync-steering",
        "--sync-prompts", "--check-health", "--components",
    )]

    if sync_steering_flag:
        return sync_steering()
    if sync_prompts_flag:
        return sync_prompts()
    if check_health_flag:
        return check_health()

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
        return generate_all(dry_run)

    # Named project or '.'
    if args and not Path(args[0]).suffix:
        candidate = args[0]
        if candidate == "." or not Path(candidate).exists():
            try:
                proj_dir = resolve_project(candidate)
                crews_config = proj_dir / ".crews" / "crew.yaml"
                if crews_config.exists():
                    print(f"Building: {proj_dir.name}")
                    with open(crews_config, encoding="utf-8") as f:
                        crew_cfg = yaml.safe_load(f) or {}
                    fleet_cfg = load_fleet_config()
                    agents = build_single_project(proj_dir, crew_cfg, fleet_cfg, dry_run)
                    print(f"Generated {len(agents)} agents at {proj_dir / '.kiro' / 'agents'}/")
                    return
            except SystemExit:
                pass

    # Legacy: direct crew.yaml path
    crew_path = Path(args[0]) if args else Path(".kiro/crew.yaml")
    if not crew_path.exists():
        if not args and Path(".crews/crew.yaml").exists():
            try:
                resolve_project(".")
                sys.argv = [sys.argv[0], "."] + (["--dry-run"] if dry_run else [])
                return main()
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
    sibling_yamls = sorted(f for f in crew_path.parent.glob("*.yaml") if f != crew_path and f.stem != "crew")

    agents = []
    if full_mode:
        for crew_file in sorted(crews_dir.glob("*.yaml")):
            print(f"Generating from: {crew_file}")
            agents.extend(generate(crew_file, output_dir, dry_run))
    else:
        print(f"Generating from: {crew_path}")
        agents = generate(crew_path, output_dir, dry_run)
        for sibling in sibling_yamls:
            print(f"Generating from: {sibling}")
            agents.extend(generate(sibling, output_dir, dry_run))

    print(f"Generated {len(agents)} agents: {', '.join(agents)}")

    if not dry_run:
        kiro_dir = output_dir.parent
        crew_sources = sorted(crews_dir.glob("*.yaml")) if full_mode else ([crew_path] + sibling_yamls)
        shared_names = collect_shared_agents(crew_sources)
        synthesize_dispatcher(crew_sources, shared_names, kiro_dir, dry_run=dry_run)
        if shared_names:
            inject_subagents_into_orchestrators(shared_names, kiro_dir)
        print(f"Output: {output_dir}/")


if __name__ == "__main__":
    main()
