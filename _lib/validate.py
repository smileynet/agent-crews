"""Validation functions for crew hierarchy and fleet coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from _lib import get_architypes


def validate_coverage(fleet: dict):
    """Warn about refused keywords that no assigned sibling crew handles.

    Only warns when at least one sibling crew's handles list contains a keyword
    in the same domain, suggesting a vocabulary mismatch. Deliberately missing
    crews (no sibling assigned for that domain) are not flagged.
    """
    root = Path(__file__).parent.parent
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


def validate_changelog_prerequisites(fleet: dict):
    """Warn if changelog component is enabled but CHANGELOG.md is missing in target."""
    root = Path(__file__).parent.parent
    for proj_name, proj_cfg in fleet.get("projects", {}).items():
        if proj_cfg.get("self_hosted"):
            continue
        behavior = proj_cfg.get("behavior", {})
        changelog_cfg = behavior.get("changelog")
        if changelog_cfg is None:
            continue
        proj_dir = root / "projects" / proj_name
        if proj_dir.exists() and not (proj_dir / "CHANGELOG.md").exists():
            print(f"  ⚠️  {proj_name}: changelog component enabled but no CHANGELOG.md (run crew-creator to scaffold)", file=sys.stderr)


def validate_hierarchy(crew_path: Path, crew: dict):
    """Validate 3-level hierarchy: dispatcher→orchestrator→worker. No lateral dispatch."""
    orchestrator_names = set()
    worker_names = set()
    dispatcher_names = set()

    for archetype in get_architypes(crew):
        atype = archetype.get("type", "worker")
        for agent_cfg in archetype.get("agents", []):
            name = agent_cfg["name"]
            if atype == "dispatcher":
                dispatcher_names.add(name)
            elif atype == "orchestrator":
                orchestrator_names.add(name)
            else:
                worker_names.add(name)

    errors = []

    for archetype in get_architypes(crew):
        atype = archetype.get("type", "worker")
        for agent_cfg in archetype.get("agents", []):
            name = agent_cfg["name"]
            tools = agent_cfg.get("tools", [])

            # Rule 1: Workers must NOT have subagent
            if atype == "worker" and "subagent" in tools:
                errors.append(f"{name}: worker has 'subagent' tool (workers cannot delegate)")

            # Rule 2: Orchestrators cannot target other orchestrators
            if atype == "orchestrator":
                available = (agent_cfg.get("toolsSettings", {})
                             .get("subagent", {})
                             .get("availableAgents", []))
                # Also check crew-level toolsSettings
                arch_available = (archetype.get("toolsSettings", {})
                                  .get("crew", {})
                                  .get("availableAgents", []))
                all_targets = set(available or arch_available)
                bad_targets = all_targets & (orchestrator_names | dispatcher_names)
                if bad_targets:
                    errors.append(f"{name}: orchestrator dispatches to orchestrator(s) {bad_targets} (must only target workers)")

            # Rule 3 (warning): Orchestrators should not have read
            if atype == "orchestrator" and "read" in tools:
                print(f"  ⚠️  {crew_path.name}: {name} has 'read' tool (orchestrators should delegate reading to workers)", file=sys.stderr)

    if errors:
        print(f"\n❌ Hierarchy violation in {crew_path.name}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
