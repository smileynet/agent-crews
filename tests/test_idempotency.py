"""Idempotency test: building twice produces identical output."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from _lib.build import generate
from _lib.utils import build_sibling_map


@pytest.fixture
def base_crews_dir():
    return Path(__file__).parent.parent / "base" / "crews"


def _build_all(crews_dir: Path, output_dir: Path) -> dict[str, str]:
    """Build all crews and return {filename: json_content}."""
    crew_files = sorted(crews_dir.glob("*.yaml"))
    siblings = build_sibling_map(crew_files)
    for cf in crew_files:
        generate(cf, output_dir, dry_run=False, sibling_crews=siblings)
    result = {}
    for f in sorted(output_dir.glob("*.json")):
        result[f.name] = f.read_text()
    return result


def test_build_is_idempotent(base_crews_dir, tmp_path):
    """Two consecutive builds produce byte-identical output."""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    out1.mkdir()
    out2.mkdir()

    result1 = _build_all(base_crews_dir, out1)
    result2 = _build_all(base_crews_dir, out2)

    assert result1.keys() == result2.keys(), "Different files generated between runs"
    for fname in result1:
        assert result1[fname] == result2[fname], f"{fname} differs between runs"


def test_build_produces_valid_json(base_crews_dir, tmp_path):
    """All generated files are valid JSON."""
    output_dir = tmp_path / "agents"
    output_dir.mkdir()
    _build_all(base_crews_dir, output_dir)

    for f in output_dir.glob("*.json"):
        data = json.loads(f.read_text())
        assert isinstance(data, dict), f"{f.name} is not a JSON object"
        assert "name" in data, f"{f.name} missing 'name' field"
