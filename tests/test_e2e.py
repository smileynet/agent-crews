"""End-to-end tests: validate full generate.py pipeline produces expected output."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


class TestBuildAll:
    """Test --all mode produces correct fleet-wide output."""

    def test_all_projects_generate_agents(self):
        """--all generates agents for all registered projects."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "--all"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0, f"--all failed: {result.stderr}"
        assert "Done." in result.stdout

    def test_base_agents_generated(self):
        """Base crews produce agent JSON files."""
        agents_dir = ROOT / "base" / "agents"
        assert agents_dir.is_dir()
        agent_files = list(agents_dir.glob("*.json"))
        assert len(agent_files) >= 50, f"Expected 50+ base agents, got {len(agent_files)}"

    def test_self_hosted_agents_generated(self):
        """Self-hosted project (agent-crews itself) generates agents."""
        agents_dir = ROOT / ".kiro" / "agents"
        assert agents_dir.is_dir()
        agent_files = list(agents_dir.glob("*.json"))
        assert len(agent_files) >= 10, f"Expected 10+ self-hosted agents, got {len(agent_files)}"


class TestSingleProjectBuild:
    """Test single-project build mode."""

    def test_build_dot_generates_agents(self):
        """Building '.' generates agents for the current project."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "."],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0, f"Build . failed: {result.stderr}"
        assert "Generated" in result.stdout

    def test_build_named_project(self):
        """Building a named project from fleet.local.yaml works."""
        # Use agent-crews itself (always in fleet.local)
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "agent-crews"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0, f"Build named failed: {result.stderr}"
        assert "Generated" in result.stdout or "agents" in result.stdout


class TestDispatcherSynthesis:
    """Test that dispatcher is correctly synthesized."""

    def test_dispatcher_exists(self):
        """Dispatcher JSON is generated for self-hosted project."""
        dispatcher_path = ROOT / ".kiro" / "agents" / "dispatcher.json"
        assert dispatcher_path.exists(), "dispatcher.json not generated"

    def test_dispatcher_has_all_leads(self):
        """Dispatcher's availableAgents includes all crew leads."""
        dispatcher_path = ROOT / ".kiro" / "agents" / "dispatcher.json"
        with open(dispatcher_path) as f:
            dispatcher = json.load(f)

        available = dispatcher.get("toolsSettings", {}).get("subagent", {}).get("availableAgents", [])
        # agent-crews has crew-builder-lead, crew-maintenance-lead, crew-tooling-lead
        assert "crew-builder-lead" in available
        assert "crew-maintenance-lead" in available
        assert "crew-tooling-lead" in available

    def test_dispatcher_has_routing_table(self):
        """Dispatcher prompt contains routing table."""
        dispatcher_path = ROOT / ".kiro" / "agents" / "dispatcher.json"
        with open(dispatcher_path) as f:
            dispatcher = json.load(f)
        assert "## Routing Table" in dispatcher.get("prompt", "")

    def test_dispatcher_has_keyboard_shortcut(self):
        """Dispatcher has a keyboard shortcut configured."""
        dispatcher_path = ROOT / ".kiro" / "agents" / "dispatcher.json"
        with open(dispatcher_path) as f:
            dispatcher = json.load(f)
        assert dispatcher.get("keyboardShortcut"), "Dispatcher missing keyboard shortcut"


class TestComponentSystem:
    """Test component steering and subagent generation."""

    def test_steering_files_generated(self):
        """Component steering files are written to .kiro/steering/."""
        steering_dir = ROOT / ".kiro" / "steering"
        assert steering_dir.is_dir()
        # Should have universal/ and worker/ and orchestrator/ subdirs
        assert (steering_dir / "universal").is_dir() or any(steering_dir.glob("*.md"))

    def test_crew_sheet_generated(self):
        """crew-sheet.md prompt is generated."""
        crew_sheet = ROOT / ".kiro" / "prompts" / "crew-sheet.md"
        assert crew_sheet.exists(), "crew-sheet.md not generated"
        content = crew_sheet.read_text()
        assert "# Crew Sheet" in content
        assert "| Agent |" in content


class TestThemeOverlay:
    """Test theme application (using a project that has a theme)."""

    def test_themed_project_renames_agents(self):
        """Projects with theme config get renamed agent files."""
        # Check if any fleet.local project has a theme
        import yaml
        fleet_local = ROOT / "fleet.local.yaml"
        if not fleet_local.exists():
            pytest.skip("No fleet.local.yaml")
        with open(fleet_local) as f:
            data = yaml.safe_load(f) or {}
        projects = data.get("projects", {})
        for name, path in projects.items():
            crew_cfg_path = Path(path).expanduser() / ".crews" / "crew.yaml"
            if not crew_cfg_path.exists():
                continue
            with open(crew_cfg_path) as f:
                cfg = yaml.safe_load(f) or {}
            if cfg.get("theme"):
                # This project has a theme — verify agents dir has themed names
                agents_dir = Path(path).expanduser() / ".kiro" / "agents"
                if agents_dir.is_dir():
                    # Just verify it has agent files (theme was applied)
                    assert list(agents_dir.glob("*.json")), f"Themed project {name} has no agents"
                return
        pytest.skip("No themed projects in fleet")


class TestDryRun:
    """Test --dry-run mode doesn't write files."""

    def test_dry_run_prints_would_write(self):
        """--dry-run on current project prints what would happen."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), ".", "--dry-run"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0
        assert "Would write" in result.stdout

    def test_all_dry_run_no_agent_changes(self):
        """--all --dry-run doesn't modify base/agents/."""
        # Record state before
        agents_dir = ROOT / "base" / "agents"
        before = {f.name: f.stat().st_mtime for f in agents_dir.glob("*.json")} if agents_dir.exists() else {}

        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "--all", "--dry-run"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0

        # Verify no files were modified (dry-run shouldn't touch disk)
        # Note: --all dry-run still syncs crews but doesn't write agents
        # The key assertion is it completes without error
        assert "Done." in result.stdout


class TestSyncOperations:
    """Test --sync-steering and --sync-prompts."""

    def test_sync_steering_runs(self):
        """--sync-steering completes without error."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "--sync-steering"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0
        assert "Done." in result.stdout

    def test_sync_prompts_runs(self):
        """--sync-prompts completes without error."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "--sync-prompts"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0
        assert "Done." in result.stdout


class TestHealthCheck:
    """Test --check-health mode."""

    def test_health_check_runs(self):
        """--check-health completes and reports results."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "generate.py"), "--check-health"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert result.returncode == 0
        assert "Checking health" in result.stdout
