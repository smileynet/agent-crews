"""Unit tests for _lib/build.py — structural assertions on generated output."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from _lib.build import build_agent, generate


@pytest.fixture
def built_agents(tmp_path):
    """Generate agents from a real crew file and return the JSON dicts."""
    root = Path(__file__).parent.parent
    crews_dir = root / "base" / "crews"
    output_dir = tmp_path / "agents"
    output_dir.mkdir()

    agents = {}
    for crew_file in sorted(crews_dir.glob("*.yaml")):
        generate(crew_file, output_dir, dry_run=False)

    for json_file in output_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        agents[data["name"]] = data
    return agents


class TestStructuralInvariants:
    """Invariants that must hold regardless of prompt content."""

    def test_workers_have_no_subagent(self, built_agents):
        """No worker agent should have the subagent tool."""
        # Workers are agents without subagent in tools (by definition)
        # But we check that agents with worker-like tool sets don't have subagent
        for name, agent in built_agents.items():
            tools = agent.get("tools", [])
            if "subagent" not in tools:
                continue
            # Agents with subagent should be orchestrators/dispatchers
            # They should NOT have write/shell (worker tools)
            has_worker_tools = {"write", "shell"} & set(tools)
            assert not has_worker_tools, (
                f"{name} has both subagent and worker tools {has_worker_tools} — hierarchy violation"
            )

    def test_orchestrators_have_subagent(self, built_agents):
        """Agents ending in '-lead' should have subagent tool."""
        for name, agent in built_agents.items():
            if name.endswith("-lead"):
                assert "subagent" in agent.get("tools", []), (
                    f"{name} is a lead but missing subagent tool"
                )

    def test_orchestrators_have_worker_table(self, built_agents):
        """Orchestrators (leads) should have a worker table in their prompt."""
        for name, agent in built_agents.items():
            if name.endswith("-lead") and "subagent" in agent.get("tools", []):
                prompt = agent.get("prompt", "")
                assert "## Your Workers" in prompt or "## Routing Table" in prompt, (
                    f"{name} is an orchestrator but has no worker/routing table in prompt"
                )

    def test_all_agents_have_name(self, built_agents):
        """Every agent JSON must have a name field."""
        for name, agent in built_agents.items():
            assert "name" in agent
            assert agent["name"] == name

    def test_all_agents_have_tools(self, built_agents):
        """Every agent should have at least one tool."""
        for name, agent in built_agents.items():
            assert agent.get("tools"), f"{name} has no tools"

    def test_no_empty_prompts(self, built_agents):
        """Agents should have non-empty prompts."""
        for name, agent in built_agents.items():
            assert agent.get("prompt", "").strip(), f"{name} has empty prompt"
