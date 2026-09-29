"""Governance tests for CURRENT_SYSTEM_CENSUS_GRAPH_V1. AUTHORITY=NONE."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "config/governance/current_system_census_graph_v1/source_v1.json"
SCHEMA = REPO / "config/governance/current_system_census_graph_v1/schema_v1.json"
VALIDATOR = REPO / "scripts/ops/validate_current_system_census_graph_v1.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_current_system_census_graph_v1", VALIDATOR
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_source_loads_and_authority_none() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert doc["artifact_id"] == "current_system_census_graph_v1"
    assert doc["authority"] == "NONE"
    assert doc["not_a_universe_ratification"] is True
    assert doc["canonical_universe_count_asserted"] is False


def test_object_conservation() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(doc["census_objects"]) == 301
    ids = [o["object_id"] for o in doc["census_objects"]]
    assert len(ids) == len(set(ids))


def test_census_discrepancies_preserved() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(doc["census_discrepancies"]) >= 6


def test_validator_passes() -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "VALIDATOR_RESULT=PASS" in result.stdout


def test_no_canonical_universe_on_objects() -> None:
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    for obj in doc["census_objects"]:
        assert obj.get("canonical_universe") is not True


def test_schema_file_present() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["artifact_id"]["const"] == "current_system_census_graph_v1"
