"""Fleet orchestration: generate all projects, load config, health checks."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

from _lib import deep_merge
from _lib.build import generate
from _lib.components import generate_components_for_project, inject_subagents_into_orchestrators
from _lib.inject import synthesize_dispatcher
from _lib.sync import sync_prompts_to_project, sync_skills_to_project, sync_steering_to_project
from _lib.utils import (
    build_sibling_map,
    collect_shared_agents,
    generate_crew_sheet,
    prune_legacy_project_md,
)
from _lib.validate import validate_changelog_prerequisites, validate_coverage
from _lib.workspace import resolve_workspace, stage_workspace


def build_single_project(
    proj_dir: Path,
    crew_cfg: dict,
    fleet_cfg: dict | None = None,
    dry_run: bool = False,
    cleanup_crews: bool = True,
) -> list[str]:
    """Build a single project from its .crews/crew.yaml config. Returns agent names."""
    root = Path(__file__).parent.parent
    base_crews_dir = root / "base" / "crews"

    proj_crews = crew_cfg.get("crews") or []
    if not proj_crews:
        sys.exit(f"  ❌ {proj_dir}: .crews/crew.yaml must declare a non-empty 'crews:' list")
    kiro_dir = proj_dir / ".kiro"
    if kiro_dir.is_symlink() and not kiro_dir.exists():
        kiro_dir.unlink()

    # Sync base crews
    crews_dir = kiro_dir / "crews"
    crews_dir.mkdir(parents=True, exist_ok=True)
    for crew_name in proj_crews:
        src = base_crews_dir / f"{crew_name}.yaml"
        if src.exists():
            shutil.copy2(src, crews_dir / src.name)
    workspace = resolve_workspace(crew_cfg, source=str(proj_dir / ".crews" / "crew.yaml"))
    if not dry_run:
        stage_workspace(proj_dir, kiro_dir, workspace)

    # Sync steering/skills/prompts BEFORE generation (prompts are read during build)
    sync_steering_to_project(kiro_dir, root)
    sync_skills_to_project(kiro_dir, root)
    sync_prompts_to_project(kiro_dir, root, workspace=workspace)
    prune_legacy_project_md(kiro_dir)

    # Generate agents
    output_dir = kiro_dir / "agents"
    if not dry_run:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    proj_crew_files = sorted(crews_dir.glob("*.yaml"))
    proj_siblings = build_sibling_map(proj_crew_files)
    agents = []
    for cf in proj_crew_files:
        agents.extend(generate(cf, output_dir, dry_run, sibling_crews=proj_siblings))

    # Crew sheet
    if not dry_run:
        crew_sheet = generate_crew_sheet(crews_dir)
        prompts_dir = kiro_dir / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        (prompts_dir / "crew-sheet.md").write_text(crew_sheet, encoding="utf-8")

    # Dispatcher + components
    shared_names = []
    if not dry_run:
        shared_names = collect_shared_agents(proj_crew_files)
        dispatcher_cfg = crew_cfg.get("dispatcher", {})
        synthesize_dispatcher(proj_crew_files, shared_names, kiro_dir, dispatcher_cfg, dry_run)

    if fleet_cfg or crew_cfg.get("behavior"):
        defaults = fleet_cfg.get("defaults", {}) if fleet_cfg else {}
        synthetic = {"projects": {proj_dir.name: crew_cfg}, "defaults": defaults}
        generate_components_for_project(proj_dir.name, kiro_dir, synthetic, dry_run)

    if not dry_run and shared_names:
        inject_subagents_into_orchestrators(shared_names, kiro_dir)

    # Cleanup temp crews dir
    if cleanup_crews and not dry_run and crews_dir.is_dir():
        shutil.rmtree(crews_dir)

    return agents



def generate_all(dry_run: bool = False):
    """Generate base crews, examples, and every fleet.local project."""
    root = Path(__file__).parent.parent
    base_crews = root / "base" / "crews"
    fleet = load_fleet_config()

    # Generate base crews (the source-of-truth catalog).
    base_output = root / "base" / "agents"
    print("Generating: base/crews/*.yaml")
    if not dry_run:
        if base_output.exists():
            shutil.rmtree(base_output)
        base_output.mkdir(parents=True, exist_ok=True)
    base_crew_files = sorted(base_crews.glob("*.yaml"))
    base_siblings = build_sibling_map(base_crew_files)
    agents = []
    for cf in base_crew_files:
        agents.extend(generate(cf, base_output, dry_run, sibling_crews=base_siblings))
    print(f"  -> {len(agents)} agents")

    # Generate every example under examples/<name>/.crews/crew.yaml using the
    # same code path as a real deployment.
    for crews_config in sorted((root / "examples").glob("*/.crews/crew.yaml")):
        proj_dir = crews_config.parent.parent
        print(f"\nGenerating example: {proj_dir.name}")
        with open(crews_config, encoding="utf-8") as f:
            crew_cfg = yaml.safe_load(f) or {}
        result = build_single_project(proj_dir, crew_cfg, fleet, dry_run)
        print(f"  -> {len(result)} agents")

    if fleet:
        validate_coverage(fleet)
        validate_changelog_prerequisites(fleet)

    # fleet.local.yaml projects (real deployments outside this repo).
    fleet_local = load_fleet_local()
    for proj_name, proj_path in fleet_local.items():
        proj_dir = Path(proj_path).expanduser()
        crews_config = proj_dir / ".crews" / "crew.yaml"
        if not crews_config.exists():
            continue
        print(f"\nGenerating (in-place): {proj_name}")
        with open(crews_config, encoding="utf-8") as f:
            crew_cfg = yaml.safe_load(f) or {}
        result = build_single_project(proj_dir, crew_cfg, fleet, dry_run)
        print(f"  -> {len(result)} agents")

    print("\nDone.")


def load_fleet_config() -> dict:
    """Load fleet config: fleet.example.yaml (committed) + fleet.yaml (local, overrides)."""
    root = Path(__file__).parent.parent
    fleet: dict = {}

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
    if name_or_path == ".":
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / ".crews" / "crew.yaml").exists():
                return cwd
            cwd = cwd.parent
        sys.exit("No .crews/crew.yaml found in cwd or parents")
    p = Path(name_or_path).expanduser()
    if p.is_dir() and (p / ".crews" / "crew.yaml").exists():
        return p
    fleet = load_fleet_local()
    if name_or_path in fleet:
        resolved = Path(fleet[name_or_path]).expanduser()
        if (resolved / ".crews" / "crew.yaml").exists():
            return resolved
        if (resolved / ".kiro" / "crew.yaml").exists():
            return resolved
    sys.exit(f"Project not found or missing .crews/crew.yaml: {name_or_path}")


