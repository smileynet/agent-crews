"""Unit tests for _lib/components.py — behavior/config resolution.

Covers the `components:` → `behavior:` public-config rename: the resolver MUST
read `behavior:` from both fleet defaults and per-project config, and MUST ignore
the old `components:` key entirely (no silent data loss, no silent fallback).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from _lib.components import resolve_component_config


def test_reads_behavior_from_project():
    fleet = {"projects": {"p": {"behavior": {"verification": {"variant": "gate"}}}}}
    assert resolve_component_config("p", fleet) == {"verification": {"variant": "gate"}}


def test_reads_behavior_from_defaults():
    fleet = {
        "defaults": {"behavior": {"git": {"variant": "checkpoint"}}},
        "projects": {"p": {}},
    }
    assert resolve_component_config("p", fleet) == {"git": {"variant": "checkpoint"}}


def test_project_overrides_defaults_per_key():
    fleet = {
        "defaults": {"behavior": {
            "verification": {"variant": "gate", "checks": {"build": "make"}},
            "git": {"variant": "checkpoint"},
        }},
        "projects": {"p": {"behavior": {
            "verification": {"checks": {"build": "cargo check"}},
        }}},
    }
    resolved = resolve_component_config("p", fleet)
    # Project overrides build, but variant + git are inherited from defaults.
    assert resolved["verification"]["variant"] == "gate"
    assert resolved["verification"]["checks"]["build"] == "cargo check"
    assert resolved["git"] == {"variant": "checkpoint"}


def test_legacy_components_key_ignored_at_project_scope():
    """The old `components:` key must not leak through after the rename."""
    fleet = {"projects": {"p": {"components": {"verification": {"variant": "gate"}}}}}
    assert resolve_component_config("p", fleet) == {}


def test_legacy_components_key_ignored_at_defaults_scope():
    fleet = {
        "defaults": {"components": {"git": {"variant": "checkpoint"}}},
        "projects": {"p": {}},
    }
    assert resolve_component_config("p", fleet) == {}


def test_missing_project_returns_empty():
    assert resolve_component_config("nope", {"projects": {}}) == {}


def test_empty_fleet_returns_empty():
    assert resolve_component_config("p", {}) == {}
