"""Unit tests for _lib/workspace.py — pure resolution + substitution logic."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from _lib.workspace import (
    DEFAULT_DURABLE,
    DEFAULT_EPHEMERAL,
    resolve_workspace,
    stage_workspace,
    substitute_workspace_placeholders,
)


class TestResolveWorkspace:
    def test_defaults_when_omitted(self):
        assert resolve_workspace({}) == {
            "ephemeral": DEFAULT_EPHEMERAL,
            "durable": DEFAULT_DURABLE,
        }

    def test_explicit_both_roots(self):
        ws = resolve_workspace({"workspace": {"ephemeral": ".work", "durable": "memory"}})
        assert ws == {"ephemeral": ".work", "durable": "memory"}

    def test_partial_ephemeral_only_rejected(self):
        with pytest.raises(SystemExit):
            resolve_workspace({"workspace": {"ephemeral": ".work"}})

    def test_partial_durable_only_rejected(self):
        with pytest.raises(SystemExit):
            resolve_workspace({"workspace": {"durable": "memory"}})

    def test_empty_workspace_dict_rejected(self):
        with pytest.raises(SystemExit):
            resolve_workspace({"workspace": {}})

    def test_non_mapping_workspace_rejected(self):
        with pytest.raises(SystemExit):
            resolve_workspace({"workspace": "scratch"})

    def test_null_value_for_root_rejected(self):
        with pytest.raises(SystemExit):
            resolve_workspace({"workspace": {"ephemeral": ".work", "durable": None}})


class TestStageWorkspace:
    def test_creates_both_roots_and_steering(self, tmp_path):
        proj = tmp_path / "proj"
        kiro = proj / ".kiro"
        kiro.mkdir(parents=True)
        ws = {"ephemeral": ".scratch", "durable": ".memory"}
        stage_workspace(proj, kiro, ws)

        assert (proj / ".scratch").is_dir()
        assert (proj / ".memory").is_dir()
        steering = (kiro / "steering" / "universal" / "workspace.md").read_text()
        assert "inclusion: always" in steering
        assert "`.scratch/`" in steering
        assert "`.memory/`" in steering
        assert "Ephemeral" in steering and "Durable" in steering

    def test_custom_paths_in_steering(self, tmp_path):
        proj = tmp_path / "proj"
        kiro = proj / ".kiro"
        kiro.mkdir(parents=True)
        stage_workspace(proj, kiro, {"ephemeral": "work", "durable": "memory"})

        steering = (kiro / "steering" / "universal" / "workspace.md").read_text()
        assert "`work/`" in steering
        assert "`memory/`" in steering
        assert "work/HANDOFF.md" in steering

    def test_idempotent(self, tmp_path):
        """Second call must not error when dirs/steering already exist."""
        proj = tmp_path / "proj"
        kiro = proj / ".kiro"
        kiro.mkdir(parents=True)
        ws = {"ephemeral": ".scratch", "durable": ".memory"}
        stage_workspace(proj, kiro, ws)
        stage_workspace(proj, kiro, ws)
        assert (proj / ".scratch").is_dir()


class TestSubstitutePlaceholders:
    def test_replaces_both_placeholders(self):
        text = "write to {{workspace.ephemeral}}/HANDOFF.md; promote to {{workspace.durable}}/"
        out = substitute_workspace_placeholders(text, {"ephemeral": ".scratch", "durable": ".memory"})
        assert out == "write to .scratch/HANDOFF.md; promote to .memory/"

    def test_no_op_when_no_placeholder(self):
        text = "no placeholders here"
        assert substitute_workspace_placeholders(text, {"ephemeral": ".x", "durable": ".y"}) == text

    def test_unknown_placeholder_untouched(self):
        text = "{{workspace.tertiary}} stays as-is"
        assert substitute_workspace_placeholders(text, {"ephemeral": ".x", "durable": ".y"}) == text
