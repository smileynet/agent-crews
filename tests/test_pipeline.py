"""Pipeline validation: components → steering → skills → agent behavior.

Validates that configured components are meaningfully passed through
the generation pipeline and produce correct artifacts.
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
COMPONENTS_DIR = ROOT / "shared" / "components"


def _build(tmp_path, crew_cfg):
    """Build a project with given crew config, return kiro_dir."""
    from _lib.fleet import build_single_project
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / ".crews").mkdir()
    (proj / ".crews" / "crew.yaml").write_text(yaml.dump(crew_cfg))
    build_single_project(proj, crew_cfg)
    return proj / ".kiro"


class TestComponentSteeringDelivery:
    """Verify components produce steering files with correct content."""

    def test_verification_component_writes_steering(self, tmp_path):
        """verification/gate produces worker/verification.md with configured checks."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"verification": {"variant": "gate", "checks": {"build": "make build", "test": "make test", "lint": "ruff check"}}},
        })
        steering = kiro / "steering" / "worker" / "verification.md"
        assert steering.exists()
        content = steering.read_text()
        assert "make build" in content
        assert "make test" in content
        assert "ruff check" in content

    def test_git_component_writes_steering(self, tmp_path):
        """git/checkpoint produces worker/git.md."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"git": {"variant": "checkpoint"}},
        })
        steering = kiro / "steering" / "worker" / "git.md"
        assert steering.exists()
        content = steering.read_text()
        assert "commit" in content.lower()

    def test_narration_component_writes_orchestrator_steering(self, tmp_path):
        """narration/verified produces orchestrator/narration.md."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"narration": "verified"},
        })
        steering = kiro / "steering" / "orchestrator" / "narration.md"
        assert steering.exists()
        content = steering.read_text()
        assert "verifier" in content.lower()

    def test_null_checks_produce_empty_placeholders(self, tmp_path):
        """Null check values substitute to empty string (not literal 'None')."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"verification": {"variant": "gate", "checks": {"build": "cargo check", "test": None, "lint": None}}},
        })
        steering = kiro / "steering" / "worker" / "verification.md"
        content = steering.read_text()
        assert "None" not in content  # Should not have literal "None"
        assert "cargo check" in content


class TestSubagentGeneration:
    """Verify component subagents are generated and wired correctly."""

    def test_verifier_generated_from_narration(self, tmp_path):
        """narration/verified generates verifier.json."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"narration": "verified"},
        })
        verifier = kiro / "agents" / "verifier.json"
        assert verifier.exists()
        data = json.loads(verifier.read_text())
        assert data["name"] == "verifier"
        assert "read" in data["tools"]

    def test_editor_generated_from_writing(self, tmp_path):
        """writing/standard generates editor.json."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"writing": "standard"},
        })
        editor = kiro / "agents" / "editor.json"
        assert editor.exists()
        data = json.loads(editor.read_text())
        assert data["name"] == "editor"

    def test_subagents_injected_into_orchestrators(self, tmp_path):
        """Component subagents appear in orchestrator availableAgents."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"narration": "verified", "writing": "standard"},
        })
        # Check general-lead has verifier and editor in availableAgents
        lead = kiro / "agents" / "general-lead.json"
        data = json.loads(lead.read_text())
        available = data.get("toolsSettings", {}).get("subagent", {}).get("availableAgents", [])
        assert "verifier" in available
        assert "editor" in available

    def test_subagents_have_no_steering_resources(self, tmp_path):
        """Verifier/editor get NO steering resources (fresh judgment)."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"narration": "verified"},
        })
        verifier = kiro / "agents" / "verifier.json"
        data = json.loads(verifier.read_text())
        resources = data.get("resources", [])
        steering_refs = [r for r in resources if "steering" in r]
        assert steering_refs == [], f"Verifier should have no steering, got: {steering_refs}"


class TestSkillDelivery:
    """Verify skills are synced and referenced correctly."""

    def test_shared_skills_synced(self, tmp_path):
        """Shared skills directory is copied to project."""
        kiro = _build(tmp_path, {"crews": ["general"]})
        skills = kiro / "skills"
        assert skills.is_dir()
        # Should have the protocol skills that agents reference
        assert (skills / "verification-protocol").is_dir() or (skills / "verification-protocol" / "SKILL.md").exists()

    def test_skill_references_resolve(self, tmp_path):
        """All skill:// references in agent JSON point to existing files."""
        kiro = _build(tmp_path, {"crews": ["general"]})
        agents_dir = kiro / "agents"
        missing = []
        for f in agents_dir.glob("*.json"):
            data = json.loads(f.read_text())
            for resource in data.get("resources", []):
                if resource.startswith("skill://"):
                    # skill:// paths are relative to project root
                    skill_path = resource.replace("skill://", "")
                    # Check in project .kiro/skills or shared/skills
                    resolved = kiro / skill_path.lstrip(".kiro/") if ".kiro/" in skill_path else ROOT / skill_path
                    alt = kiro / "skills" / Path(skill_path).name
                    if not resolved.exists() and not alt.exists():
                        # Try parent dir match
                        parts = Path(skill_path).parts
                        found = False
                        for skills_dir in [kiro / "skills", ROOT / "shared" / "skills"]:
                            for candidate in skills_dir.rglob("SKILL.md"):
                                if any(p in str(candidate) for p in parts[-2:]):
                                    found = True
                                    break
                        if not found:
                            missing.append((data["name"], resource))
        assert not missing, f"Unresolved skill references: {missing}"


class TestPlaceholderSubstitution:
    """Verify {{placeholder}} values are correctly substituted."""

    def test_notifications_channels_substituted(self, tmp_path):
        """{{notifications.channels}} in steering resolves to configured value."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"notifications": {"variant": "channels", "channels": ["toast", "slack"], "policy": "completions"}},
        })
        steering = kiro / "steering" / "orchestrator" / "notifications.md"
        assert steering.exists()
        content = steering.read_text()
        assert "toast" in content

    def test_verification_checks_substituted(self, tmp_path):
        """{{checks.build}} in steering resolves to configured command."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {"verification": {"variant": "gate", "checks": {"build": "npm run build", "test": "npm test", "lint": "eslint ."}}},
        })
        steering = kiro / "steering" / "worker" / "verification.md"
        content = steering.read_text()
        assert "npm run build" in content
        assert "npm test" in content
        assert "eslint ." in content


class TestComponentCombinations:
    """Verify multiple components work together without conflicts."""

    def test_full_component_stack(self, tmp_path):
        """All default components generate without error."""
        kiro = _build(tmp_path, {
            "crews": ["general"],
            "components": {
                "narration": "verified",
                "writing": "standard",
                "verification": {"variant": "gate", "checks": {"build": "make", "test": None, "lint": None}},
                "git": {"variant": "checkpoint"},
                "notifications": {"variant": "channels", "channels": ["toast"], "policy": "completions"},
            },
        })
        # All expected steering files exist
        assert (kiro / "steering" / "worker" / "verification.md").exists()
        assert (kiro / "steering" / "worker" / "git.md").exists()
        assert (kiro / "steering" / "worker" / "writing.md").exists()
        assert (kiro / "steering" / "orchestrator" / "narration.md").exists()
        assert (kiro / "steering" / "orchestrator" / "notifications.md").exists()
        # Subagents exist
        assert (kiro / "agents" / "verifier.json").exists()
        assert (kiro / "agents" / "editor.json").exists()

    def test_no_component_config_still_builds(self, tmp_path):
        """Project with no components: section builds cleanly."""
        kiro = _build(tmp_path, {"crews": ["general"]})
        agents_dir = kiro / "agents"
        assert len(list(agents_dir.glob("*.json"))) > 10
