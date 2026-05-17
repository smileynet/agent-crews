"""Deployment pipeline validation: every artifact deployed has a consumption path.

Tests the contract between generator output and kiro-cli runtime:
- Agents: loaded by kiro-cli from .kiro/agents/*.json
- Steering: loaded via inclusion:always frontmatter into agent context
- Skills: loaded on-demand via skill:// resource references
- Prompts: injected into welcomeMessage as @prompt-name
- Scripts: documented in steering for agent discovery
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent


def _deploy(tmp_path, cfg):
    """Deploy a full project and return kiro_dir."""
    from _lib.fleet import build_single_project
    proj = tmp_path / "deployed"
    proj.mkdir()
    (proj / ".crews").mkdir()
    (proj / ".crews" / "crew.yaml").write_text(yaml.dump(cfg))
    build_single_project(proj, cfg)
    return proj


FULL_STACK_CFG = {
    "crews": ["general", "bug-fix"],
    "components": {
        "narration": "verified",
        "writing": "standard",
        "verification": {"variant": "gate", "checks": {"build": "make", "test": "pytest", "lint": "ruff check"}},
        "git": {"variant": "checkpoint"},
        "notifications": {"variant": "channels", "channels": ["toast"], "policy": "completions"},
        "completion": "standard",
        "signaling": "standard",
        "sanity_gate": "assumption-register",
        "search": {"variant": "layered", "sources": ["local", "web"]},
        "task_tracking": {"variant": "soft-hard", "backend": "todo-tool"},
        "decisions": "progressive",
        "troubleshooting": {"variant": "systematic"},
        "memory": {"variant": "four-tier", "tiers": ["working", "session"]},
    },
}


class TestSkillConsumption:
    """Every synced skill must be reachable by at least one agent."""

    def test_protocol_skills_referenced(self, tmp_path):
        """Protocol skills injected by build.py are referenced by agents."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        protocol_skills = [
            "verification-protocol/SKILL.md",
            "git-protocol/SKILL.md",
            "troubleshooting-protocol/SKILL.md",
            "completion-protocol/SKILL.md",
        ]
        all_resources = set()
        for f in (kiro / "agents").glob("*.json"):
            data = json.loads(f.read_text())
            all_resources.update(data.get("resources", []))

        for skill in protocol_skills:
            ref = f"skill://.kiro/skills/{skill}"
            assert ref in all_resources, f"Protocol skill {skill} not referenced by any agent"

    def test_all_skill_references_resolve(self, tmp_path):
        """Every skill:// reference in agent JSON points to an existing file."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        missing = []
        for f in (kiro / "agents").glob("*.json"):
            data = json.loads(f.read_text())
            for r in data.get("resources", []):
                if not r.startswith("skill://"):
                    continue
                path = r.replace("skill://", "")
                if not (proj / path).exists():
                    missing.append((data["name"], r))
        assert not missing, f"Unresolved skill references: {missing}"

    def test_crew_defined_skill_refs_resolve(self, tmp_path):
        """Skills referenced in crew YAML (not just protocol) also resolve."""
        proj = _deploy(tmp_path, {"crews": ["general"], "components": {}})
        kiro = proj / ".kiro"
        for f in (kiro / "agents").glob("*.json"):
            data = json.loads(f.read_text())
            for r in data.get("resources", []):
                if r.startswith("skill://"):
                    path = r.replace("skill://", "")
                    assert (proj / path).exists(), f"{data['name']}: {r} does not resolve"


class TestSteeringConsumption:
    """Steering files must have valid frontmatter for kiro-cli to load them."""

    def test_all_steering_has_inclusion_frontmatter(self, tmp_path):
        """Every steering .md file has inclusion: always frontmatter."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        missing_frontmatter = []
        for f in (kiro / "steering").rglob("*.md"):
            content = f.read_text()
            if not content.startswith("---"):
                missing_frontmatter.append(str(f.relative_to(kiro / "steering")))
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                missing_frontmatter.append(str(f.relative_to(kiro / "steering")))
                continue
            fm = yaml.safe_load(parts[1])
            if not fm or fm.get("inclusion") != "always":
                missing_frontmatter.append(str(f.relative_to(kiro / "steering")))
        assert not missing_frontmatter, f"Steering without inclusion:always: {missing_frontmatter}"

    def test_component_steering_has_content(self, tmp_path):
        """Component-generated steering files are non-empty and meaningful."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        expected = [
            ("worker/verification.md", "Gate workflow"),
            ("worker/git.md", "commit"),
            ("worker/troubleshooting.md", "Investigate"),
            ("worker/writing.md", "Style"),
            ("orchestrator/narration.md", "Narrate"),
            ("orchestrator/notifications.md", "Channels"),
            ("orchestrator/decisions.md", "Decision"),
            ("orchestrator/task.md", "Track"),
            ("orchestrator/memory.md", "Tier"),
            ("universal/signaling.md", "DONE"),
            ("universal/sanity.md", "Assumption"),
            ("universal/completion.md", "Completion"),
        ]
        for path, keyword in expected:
            full = kiro / "steering" / path
            assert full.exists(), f"Missing: {path}"
            content = full.read_text()
            assert keyword.lower() in content.lower(), f"{path} missing expected keyword '{keyword}'"


class TestScriptConsumption:
    """Deployed scripts must be documented in steering for agent discovery."""

    def test_scripts_documented_in_steering(self, tmp_path):
        """Every deployed script appears in universal/scripts.md."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        scripts_dir = kiro / "scripts"
        if not scripts_dir.is_dir():
            pytest.skip("No scripts deployed")
        scripts_md = kiro / "steering" / "universal" / "scripts.md"
        assert scripts_md.exists(), "scripts.md steering not generated"
        content = scripts_md.read_text()
        for script in scripts_dir.iterdir():
            assert script.name in content, f"Script {script.name} not documented in scripts.md"

    def test_scripts_are_executable(self, tmp_path):
        """Deployed scripts have valid shebang or are shell scripts."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        scripts_dir = proj / ".kiro" / "scripts"
        if not scripts_dir.is_dir():
            pytest.skip("No scripts deployed")
        for script in scripts_dir.iterdir():
            content = script.read_text()
            assert content.startswith("#!") or content.strip(), f"{script.name} is empty or has no shebang"


class TestPromptConsumption:
    """Prompts must be discoverable by agents via welcomeMessage injection."""

    def test_prompts_injected_into_welcome(self, tmp_path):
        """Shared prompts appear as @prompt-name in orchestrator welcomeMessages."""
        proj = _deploy(tmp_path, FULL_STACK_CFG)
        kiro = proj / ".kiro"
        prompts = [p.stem for p in (kiro / "prompts").glob("*.md") if p.stem != "crew-sheet"]
        # At least one orchestrator should reference prompts
        found_any = False
        for f in (kiro / "agents").glob("*.json"):
            data = json.loads(f.read_text())
            wm = data.get("welcomeMessage", "")
            if any(f"@{p}" in wm for p in prompts):
                found_any = True
                break
        assert found_any, "No orchestrator has prompt references in welcomeMessage"

    def test_crew_sheet_has_all_agents(self, tmp_path):
        """crew-sheet.md lists every generated agent."""
        proj = _deploy(tmp_path, {"crews": ["general"]})
        kiro = proj / ".kiro"
        crew_sheet = (kiro / "prompts" / "crew-sheet.md").read_text()
        # Check a few known general crew agents
        assert "general-lead" in crew_sheet
        assert "builder" in crew_sheet


class TestAllowedCommandsGap:
    """Document the known gap: allowed_commands not merged into toolsSettings."""

    def test_allowed_commands_not_in_agent_json(self, tmp_path):
        """KNOWN GAP: component allowed_commands are NOT merged into agent toolsSettings.

        This test documents the current behavior. When this is implemented,
        change the assertion to verify commands ARE present.
        """
        proj = _deploy(tmp_path, {
            "crews": ["general"],
            "components": {"verification": {"variant": "gate", "checks": {"build": "cargo check", "test": "cargo test", "lint": "cargo clippy"}}},
        })
        kiro = proj / ".kiro"
        # Check if any worker has allowedCommands with the configured values
        has_commands = False
        for f in (kiro / "agents").glob("*.json"):
            data = json.loads(f.read_text())
            cmds = data.get("toolsSettings", {}).get("execute_bash", {}).get("allowedCommands", [])
            if "cargo check" in cmds:
                has_commands = True
        # Currently NOT implemented — this documents the gap
        assert not has_commands, (
            "allowed_commands are now being merged! Update this test to assert they ARE present."
        )


class TestSubagentIsolation:
    """Component-generated subagents must have fresh context (no steering)."""

    def test_component_verifier_no_resources(self, tmp_path):
        """Component-generated verifier has empty resources (fresh judgment)."""
        proj = _deploy(tmp_path, {
            "crews": ["general"],  # general has no crew-defined verifier
            "components": {"narration": "verified"},
        })
        kiro = proj / ".kiro"
        verifier = json.loads((kiro / "agents" / "verifier.json").read_text())
        assert verifier.get("resources", []) == [], (
            f"Component verifier should have no resources, got: {verifier.get('resources')}"
        )

    def test_crew_defined_verifier_keeps_resources(self, tmp_path):
        """Crew-defined verifier (bug-fix) retains its configured resources."""
        proj = _deploy(tmp_path, {
            "crews": ["general", "bug-fix"],  # bug-fix defines its own verifier
            "components": {"narration": "verified"},
        })
        kiro = proj / ".kiro"
        verifier = json.loads((kiro / "agents" / "verifier.json").read_text())
        # bug-fix crew's verifier has resources (it's a full worker, not component-generated)
        assert len(verifier.get("resources", [])) > 0, (
            "Crew-defined verifier should keep its resources"
        )
