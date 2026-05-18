"""Unit tests for _lib/validate.py — hierarchy validation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from _lib.validate import validate_changelog_prerequisites, validate_hierarchy


def _crew(architypes):
    return {"architypes": architypes}


def _arch(type_, agents):
    return {"type": type_, "agents": agents}


def _agent(name, tools=None, **kwargs):
    a = {"name": name}
    if tools:
        a["tools"] = tools
    a.update(kwargs)
    return a


class TestValidateHierarchy:
    """Tests for the 3-level hierarchy rules."""

    def test_valid_hierarchy_passes(self):
        """Clean crew with dispatcher→orchestrator→worker passes without error."""
        crew = _crew([
            _arch("dispatcher", [_agent("dispatcher", ["subagent", "read"])]),
            _arch("orchestrator", [_agent("lead", ["subagent"])]),
            _arch("worker", [_agent("builder", ["read", "write", "shell"])]),
        ])
        # Should not raise
        validate_hierarchy(Path("test.yaml"), crew)

    def test_worker_with_subagent_exits(self):
        """Workers must NOT have subagent tool."""
        crew = _crew([
            _arch("worker", [_agent("bad-worker", ["read", "write", "subagent"])]),
        ])
        with pytest.raises(SystemExit):
            validate_hierarchy(Path("test.yaml"), crew)

    def test_orchestrator_targeting_orchestrator_exits(self):
        """Orchestrators cannot dispatch to other orchestrators."""
        crew = _crew([
            _arch("orchestrator", [
                _agent("lead-a", ["subagent"], toolsSettings={"subagent": {"availableAgents": ["lead-b"]}}),
                _agent("lead-b", ["subagent"]),
            ]),
        ])
        with pytest.raises(SystemExit):
            validate_hierarchy(Path("test.yaml"), crew)

    def test_orchestrator_with_read_warns(self, capsys):
        """Orchestrators with read tool get a warning (not an error)."""
        crew = _crew([
            _arch("orchestrator", [_agent("lead", ["subagent", "read"])]),
            _arch("worker", [_agent("worker", ["read", "write"])]),
        ])
        validate_hierarchy(Path("test.yaml"), crew)
        captured = capsys.readouterr()
        assert "read" in captured.err
        assert "orchestrators should delegate" in captured.err

    def test_dispatcher_with_subagent_is_fine(self):
        """Dispatchers are allowed subagent (they route to orchestrators)."""
        crew = _crew([
            _arch("dispatcher", [_agent("dispatcher", ["subagent", "read"])]),
            _arch("orchestrator", [_agent("lead", ["subagent"])]),
        ])
        validate_hierarchy(Path("test.yaml"), crew)

    def test_empty_crew_passes(self):
        """Empty architypes list doesn't crash."""
        validate_hierarchy(Path("test.yaml"), {"architypes": []})

    def test_archetypes_spelling_works(self):
        """Both 'architypes' and 'archetypes' spellings are supported."""
        crew = {"archetypes": [
            _arch("worker", [_agent("w1", ["read", "write"])]),
        ]}
        validate_hierarchy(Path("test.yaml"), crew)


class TestValidateChangelogPrerequisites:
    """Asserts the public-config rename took effect: the legacy `components:` key
    MUST NOT trigger the missing-CHANGELOG warning anymore (warnings come from
    `behavior.changelog`).
    """

    def test_no_warn_when_legacy_components_key(self, capsys):
        validate_changelog_prerequisites({
            "projects": {"demo": {"components": {"changelog": "standard"}}},
        })
        assert "CHANGELOG.md" not in capsys.readouterr().err

    def test_no_warn_when_behavior_changelog_absent(self, capsys):
        validate_changelog_prerequisites({"projects": {"demo": {"behavior": {}}}})
        assert "CHANGELOG.md" not in capsys.readouterr().err

    def test_no_warn_for_self_hosted(self, capsys):
        validate_changelog_prerequisites({
            "projects": {"demo": {
                "self_hosted": True,
                "behavior": {"changelog": "standard"},
            }},
        })
        assert "CHANGELOG.md" not in capsys.readouterr().err
