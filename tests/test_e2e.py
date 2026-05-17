"""End-to-end tests: validate full generate.py pipeline produces expected output.

All tests use isolated tmp directories with synthetic fixtures.
No test depends on production state (fleet.local.yaml, .kiro/, etc).
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
BASE_CREWS = ROOT / "base" / "crews"
SHARED = ROOT / "shared"


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project with .crews/crew.yaml pointing to general crew."""
    proj = tmp_path / "test-project"
    proj.mkdir()
    crews_dir = proj / ".crews"
    crews_dir.mkdir()
    (crews_dir / "crew.yaml").write_text(yaml.dump({"crews": ["general"]}))
    return proj



@pytest.fixture
def multi_crew_project(tmp_path):
    """Create a project with multiple crews for dispatcher/routing tests."""
    proj = tmp_path / "multi-crew"
    proj.mkdir()
    crews_dir = proj / ".crews"
    crews_dir.mkdir()
    (crews_dir / "crew.yaml").write_text(yaml.dump({
        "crews": ["general", "crew-builder", "crew-tooling"],
    }))
    return proj


@pytest.fixture
def project_with_behavior(tmp_path):
    """Create a project with component config."""
    proj = tmp_path / "comp-project"
    proj.mkdir()
    crews_dir = proj / ".crews"
    crews_dir.mkdir()
    (crews_dir / "crew.yaml").write_text(yaml.dump({
        "crews": ["general"],
        "behavior": {
            "verification": {"variant": "gate", "checks": {"build": "echo ok"}},
            "git": {"variant": "checkpoint"},
        },
    }))
    return proj


def _build_project(proj_dir: Path, dry_run: bool = False) -> list[str]:
    """Build a project using the library directly (no subprocess)."""
    from _lib.fleet import build_single_project
    crews_config = proj_dir / ".crews" / "crew.yaml"
    with open(crews_config) as f:
        crew_cfg = yaml.safe_load(f) or {}
    return build_single_project(proj_dir, crew_cfg, fleet_cfg=None, dry_run=dry_run)


class TestSingleProjectBuild:
    """Test building a single project from .crews/crew.yaml."""

    def test_generates_agents(self, project_dir):
        """Building a project produces agent JSON files."""
        agents = _build_project(project_dir)
        assert len(agents) > 10, f"Expected 10+ agents, got {len(agents)}"

    def test_agents_are_valid_json(self, project_dir):
        """All generated agent files are valid JSON with required fields."""
        _build_project(project_dir)
        agents_dir = project_dir / ".kiro" / "agents"
        for f in agents_dir.glob("*.json"):
            data = json.loads(f.read_text())
            assert "name" in data
            assert "tools" in data
            assert data["name"] == f.stem

    def test_creates_kiro_structure(self, project_dir):
        """Build creates .kiro/ with agents, prompts, steering."""
        _build_project(project_dir)
        kiro = project_dir / ".kiro"
        assert (kiro / "agents").is_dir()
        assert (kiro / "prompts").is_dir()
        assert (kiro / "steering").is_dir()

    def test_cleans_up_temp_crews(self, project_dir):
        """Temp .kiro/crews/ directory is removed after build."""
        _build_project(project_dir)
        assert not (project_dir / ".kiro" / "crews").exists()

    def test_dry_run_no_files_written(self, project_dir):
        """Dry run produces agent names but writes nothing."""
        agents = _build_project(project_dir, dry_run=True)
        assert len(agents) > 0
        assert not (project_dir / ".kiro" / "agents").exists()


class TestDispatcherSynthesis:
    """Test dispatcher is correctly generated from crew composition."""

    def test_dispatcher_generated(self, project_dir):
        """Dispatcher JSON is created."""
        _build_project(project_dir)
        dispatcher = project_dir / ".kiro" / "agents" / "dispatcher.json"
        assert dispatcher.exists()

    def test_dispatcher_has_subagent_tool(self, project_dir):
        """Dispatcher has subagent in its tools."""
        _build_project(project_dir)
        with open(project_dir / ".kiro" / "agents" / "dispatcher.json") as f:
            data = json.load(f)
        assert "subagent" in data["tools"]

    def test_dispatcher_routes_to_leads(self, multi_crew_project):
        """Dispatcher's availableAgents includes all crew leads."""
        _build_project(multi_crew_project)
        with open(multi_crew_project / ".kiro" / "agents" / "dispatcher.json") as f:
            data = json.load(f)
        available = data["toolsSettings"]["subagent"]["availableAgents"]
        # general crew has general-lead, crew-builder has crew-builder-lead, etc.
        assert "general-lead" in available
        assert "crew-builder-lead" in available
        assert "crew-tooling-lead" in available

    def test_dispatcher_has_routing_table(self, project_dir):
        """Dispatcher prompt contains a routing table."""
        _build_project(project_dir)
        with open(project_dir / ".kiro" / "agents" / "dispatcher.json") as f:
            data = json.load(f)
        assert "## Routing Table" in data["prompt"]

    def test_dispatcher_has_keyboard_shortcut(self, project_dir):
        """Dispatcher gets default keyboard shortcut."""
        _build_project(project_dir)
        with open(project_dir / ".kiro" / "agents" / "dispatcher.json") as f:
            data = json.load(f)
        assert data.get("keyboardShortcut") == "ctrl+shift+d"


class TestComponentSystem:
    """Test component steering and subagent generation."""

    def test_steering_files_written(self, project_with_behavior):
        """Components write steering files to appropriate subdirs."""
        _build_project(project_with_behavior)
        steering = project_with_behavior / ".kiro" / "steering"
        # verification and git components write to worker/ or universal/
        md_files = list(steering.rglob("*.md"))
        assert len(md_files) > 0, "No steering files generated"

    def test_crew_sheet_generated(self, project_dir):
        """crew-sheet.md prompt is generated with agent table."""
        _build_project(project_dir)
        crew_sheet = project_dir / ".kiro" / "prompts" / "crew-sheet.md"
        assert crew_sheet.exists()
        content = crew_sheet.read_text()
        assert "# Crew Sheet" in content
        assert "| Agent |" in content


class TestWorkspace:
    """Workspace contract: roots staged, steering emitted, prompts substituted."""

    def test_default_workspace_dirs_created(self, project_dir):
        _build_project(project_dir)
        assert (project_dir / ".scratch").is_dir()
        assert (project_dir / ".memory").is_dir()

    def test_workspace_steering_emitted(self, project_dir):
        _build_project(project_dir)
        steering = (project_dir / ".kiro" / "steering" / "universal" / "workspace.md").read_text()
        assert "`.scratch/`" in steering
        assert "`.memory/`" in steering
        assert "Ephemeral" in steering and "Durable" in steering

    def test_handoff_prompt_substitutes_ephemeral_path(self, project_dir):
        _build_project(project_dir)
        handoff = (project_dir / ".kiro" / "prompts" / "handoff.md").read_text()
        assert "{{workspace.ephemeral}}" not in handoff
        assert ".scratch/HANDOFF.md" in handoff

    def test_custom_workspace_roots(self, tmp_path):
        proj = tmp_path / "custom-ws"
        proj.mkdir()
        (proj / ".crews").mkdir()
        (proj / ".crews" / "crew.yaml").write_text(yaml.dump({
            "crews": ["general"],
            "workspace": {"ephemeral": ".work", "durable": "memory"},
        }))
        _build_project(proj)
        assert (proj / ".work").is_dir()
        assert (proj / "memory").is_dir()
        handoff = (proj / ".kiro" / "prompts" / "handoff.md").read_text()
        assert ".work/HANDOFF.md" in handoff

    def test_partial_workspace_rejected(self, tmp_path):
        proj = tmp_path / "bad-ws"
        proj.mkdir()
        (proj / ".crews").mkdir()
        (proj / ".crews" / "crew.yaml").write_text(yaml.dump({
            "crews": ["general"],
            "workspace": {"ephemeral": ".work"},
        }))
        with pytest.raises(SystemExit):
            _build_project(proj)

    def test_missing_crews_rejected(self, tmp_path):
        proj = tmp_path / "no-crews"
        proj.mkdir()
        (proj / ".crews").mkdir()
        (proj / ".crews" / "crew.yaml").write_text(yaml.dump({"persona": "personal"}))
        with pytest.raises(SystemExit):
            _build_project(proj)


class TestSyncOperations:
    """Test steering/skills/prompts sync to project."""

    def test_steering_synced(self, project_dir):
        """Shared steering files are copied to project."""
        _build_project(project_dir)
        steering = project_dir / ".kiro" / "steering"
        assert steering.is_dir()
        # Universal steering should be present
        md_files = list(steering.glob("*.md")) + list(steering.rglob("*.md"))
        assert len(md_files) > 0

    def test_skills_synced(self, project_dir):
        """Shared skills are copied to project."""
        _build_project(project_dir)
        skills = project_dir / ".kiro" / "skills"
        assert skills.is_dir()
        assert len(list(skills.iterdir())) > 0

    def test_prompts_synced(self, project_dir):
        """Shared prompts are copied to project."""
        _build_project(project_dir)
        prompts = project_dir / ".kiro" / "prompts"
        assert prompts.is_dir()
        # Should have crew-sheet + shared prompts
        assert len(list(prompts.glob("*.md"))) >= 1

    def test_project_md_skeleton_created(self, project_dir):
        """project.md skeleton is generated if missing."""
        _build_project(project_dir)
        project_md = project_dir / ".kiro" / "steering" / "project.md"
        assert project_md.exists()
        content = project_md.read_text()
        assert "inclusion: always" in content
        assert "## Scope Of This File" in content
        assert "## Runtime Boundary" in content
        assert "`.kiro/` is the deployed runtime surface" in content
        assert "`.crews/` is the project config surface" in content

    def test_legacy_project_md_skeleton_is_upgraded(self, project_dir):
        """Untouched legacy project.md skeletons are upgraded in place."""
        project_md = project_dir / ".kiro" / "steering" / "project.md"
        project_md.parent.mkdir(parents=True, exist_ok=True)
        project_md.write_text("""---
inclusion: always
---

# test-project

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
        _build_project(project_dir)
        content = project_md.read_text()
        assert "## Scope Of This File" in content
        assert "## Runtime Boundary" in content

class TestHierarchyEnforcement:
    """Test that hierarchy rules are enforced during build."""

    def test_workers_have_no_subagent(self, project_dir):
        """No worker agent gets subagent tool in generated output."""
        _build_project(project_dir)
        agents_dir = project_dir / ".kiro" / "agents"
        for f in agents_dir.glob("*.json"):
            data = json.loads(f.read_text())
            tools = set(data.get("tools", []))
            if "subagent" in tools:
                # Must not also have write/shell (worker tools)
                assert not ({"write", "shell"} & tools), (
                    f"{data['name']} has subagent + worker tools"
                )

    def test_orchestrators_have_worker_table(self, project_dir):
        """Orchestrators (leads) have worker tables injected."""
        _build_project(project_dir)
        agents_dir = project_dir / ".kiro" / "agents"
        for f in agents_dir.glob("*-lead.json"):
            data = json.loads(f.read_text())
            if "subagent" in data.get("tools", []):
                prompt = data.get("prompt", "")
                assert "## Your Workers" in prompt or "## Routing Table" in prompt, (
                    f"{data['name']} missing worker/routing table"
                )


class TestIdempotency:
    """Test that builds are deterministic."""

    def test_two_builds_identical(self, project_dir):
        """Building the same project twice produces identical output."""
        _build_project(project_dir)
        first = {}
        agents_dir = project_dir / ".kiro" / "agents"
        for f in sorted(agents_dir.glob("*.json")):
            first[f.name] = f.read_text()

        # Rebuild (build_single_project cleans agents dir)
        _build_project(project_dir)
        for f in sorted(agents_dir.glob("*.json")):
            assert f.read_text() == first[f.name], f"{f.name} differs between builds"
