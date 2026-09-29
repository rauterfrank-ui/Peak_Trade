"""Currency and authority tests for CURRENT_LAW_IMPACT_MAP_V1. AUTHORITY=NONE."""

from __future__ import annotations

import copy
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "scripts/ops/current_law_impact_map_v1.py"
MASTER_V2 = REPO / "src/trading/master_v2"


def _load():
    spec = importlib.util.spec_from_file_location("current_law_impact_map_v1", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MAP = _load()


def _doc():
    return MAP._load_json(MAP.SOURCE_PATH)


def test_schema_and_authority_constants() -> None:
    doc = _doc()
    assert doc["map_authority"] == "NONE"
    assert doc["authority_effect"] == "NONE"
    assert doc["law_reference_is_normative"] is False
    assert doc["bootstrap_exhaustive"] is False
    assert doc["normalize_unknown_to_current"] is False
    assert MAP.validate_schema(doc, MAP._load_json(MAP.SCHEMA_PATH)) == []


def test_deterministic_regeneration() -> None:
    doc = _doc()
    assert MAP.render_views(doc) == MAP.render_views(doc)


def test_generated_files_clean() -> None:
    assert MAP.derived_drift(_doc(), REPO) == []


def test_forbidden_normative_key_rejected() -> None:
    doc = copy.deepcopy(_doc())
    doc["law_references"][0]["normative_text"] = "forbidden"
    errors: list[str] = []
    MAP._scan_forbidden_keys(doc, "source", errors)
    assert any("normative_text" in e for e in errors)


def test_stale_source_sha256_detected() -> None:
    doc = copy.deepcopy(_doc())
    doc["law_references"][0]["source_sha256"] = "0" * 64
    errors = MAP.validate_law_references(doc, REPO)
    assert any("STALE source_sha256" in e for e in errors)


def test_unknown_pin_preserved() -> None:
    doc = _doc()
    unk_ids = {item["id"] for item in doc["unknown_relations"]}
    assert "unk_mt_l5_nullline_identity" in unk_ids
    view = MAP.render_views(doc)["unknown_and_conflict"]
    assert "unk_mt_l5_nullline_identity" in view
    assert "UNKNOWN_RELATION" in view


def test_missing_required_unknown_fails() -> None:
    doc = copy.deepcopy(_doc())
    doc["unknown_relations"] = [
        u for u in doc["unknown_relations"] if u["id"] != "unk_mt_l5_nullline_identity"
    ]
    errors = MAP.validate_unknown_and_conflict(doc)
    assert any("unk_mt_l5_nullline_identity" in e for e in errors)


def test_violated_current_forbidden_in_map() -> None:
    doc = copy.deepcopy(_doc())
    doc["semantic_objects"][0]["current_status"] = "VIOLATED_CURRENT"
    errors = MAP.validate_semantic_objects(doc, REPO)
    assert any("VIOLATED_CURRENT forbidden" in e for e in errors)


def test_no_map_impact_without_adjudication_fails() -> None:
    declaration = {
        "authority_effect": "NONE",
        "selector_used_as_law_impact_authority": False,
        "verdict": "NO_LAW_IMPACT",
        "reason": "test",
        "evidence_refs": ["tests/ops/test_current_law_impact_map_v1.py"],
        "changed_paths": ["src/ops/foo.py"],
        "changed_paths_sha256": MAP.paths_sha256(["src/ops/foo.py"]),
    }
    errors = MAP.evaluate_impact(
        ["src/ops/foo.py"],
        declaration,
        surfaces=[],
        source_changed=False,
        derived_clean=True,
    )
    assert any("undeterminable" in e for e in errors)


def test_master_v2_unchanged_in_diff_against_main() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD", "--", "src/trading/master_v2"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""


def test_runtime_untracked_not_in_diff() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD", "--", "runtime/"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""


def test_surface_expansion_counts_and_census_meta() -> None:
    doc = _doc()
    assert len(doc["law_references"]) >= 22
    assert len(doc["semantic_objects"]) >= 26
    assert len(doc.get("unclassified_current_surfaces", [])) > 0
    assert doc["surface_census_meta"]["authority"] == "NONE"
    assert doc["surface_census_meta"]["bootstrap_exhaustive"] is False
    assert len(doc.get("semantic_divergence_index", [])) >= 2
    assert doc["surface_census_meta"]["census_id"] == "UCS_EVIDENCE_BINDING_V1"


def test_divergence_index_forbids_violated_in_validator() -> None:
    doc = copy.deepcopy(_doc())
    doc["semantic_divergence_index"][0]["adjudication"] = "VIOLATED_CURRENT"
    errors = MAP.validate_semantic_divergence_index(doc)
    assert any("VIOLATED_CURRENT forbidden" in e for e in errors)


def test_generated_surface_census_view_present() -> None:
    views = MAP.render_views(_doc())
    assert "surface_census" in views
    assert "SEM-SURF-DIV-00001" in views["surface_census"]
    assert "UNCLASSIFIED" in views["surface_census"]


def test_impact_engine_tier1_unclassified() -> None:
    from scripts.ops.law_map_v1.impact_v1 import evaluate_changed_paths

    doc = _doc()
    report = evaluate_changed_paths(
        doc,
        ["src/ops/current_productive_new_unknown_surface_v1.py"],
        candidate_surfaces=[],
    )
    assert report.unclassified_surfaces


def test_numeric_equality_not_used_as_identity_edge() -> None:
    doc = _doc()
    for edge in doc["impact_edges"]:
        assert edge["edge_class"] != "IDENTITY_EQUIVALENCE"
