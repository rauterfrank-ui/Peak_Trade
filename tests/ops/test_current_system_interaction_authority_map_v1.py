"""Currency tests for CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1. AUTHORITY=NONE."""

from __future__ import annotations

import copy
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "scripts/ops/current_system_interaction_authority_map_v1.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "current_system_interaction_authority_map_v1", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MAP = _load()


def _doc():
    return MAP._load_json(MAP.SOURCE_PATH)


def test_schema_valid() -> None:
    doc = _doc()
    assert MAP.validate_schema(doc, MAP._load_json(MAP.SCHEMA_PATH)) == []


def test_deterministic_regeneration() -> None:
    doc = _doc()
    assert MAP.render_views(doc) == MAP.render_views(doc)


def test_generated_files_clean() -> None:
    assert MAP.derived_drift(_doc(), REPO) == []


def test_proven_current_without_evidence_fails() -> None:
    doc = copy.deepcopy(_doc())
    for domain in doc["domains"]:
        if domain["status"] == "PROVEN_CURRENT":
            domain["evidence_refs"] = []
            break
    errors = MAP.validate_evidence(doc, REPO)
    assert any("missing evidence anchor" in error for error in errors)


def test_unknown_stays_unknown() -> None:
    view = MAP.render_views(_doc())["authority"]
    assert "id=sealed_venue_number_29p class=UNKNOWN" in view
    assert MAP.project_status("UNKNOWN") == "UNKNOWN"


def test_conflicting_stays_conflicting() -> None:
    view = MAP.render_views(_doc())["authority"]
    assert "id=b05_vs_singular_risk_owner class=CONFLICTING" in view
    assert MAP.project_status("CONFLICTING") == "CONFLICTING"


def test_partial_stays_partial() -> None:
    view = MAP.render_views(_doc())["authority"]
    assert "id=p5_bind_without_cutover class=PARTIAL" in view
    assert MAP.project_status("PARTIAL") == "PARTIAL"


def test_historical_default_is_not_promoted_to_current() -> None:
    section = MAP.render_views(_doc())["parameter_lineage"].split(
        "## historical_crs_limits_25_500", 1
    )[1]
    section = section.split("## ", 1)[0]
    assert "semantic_class=HISTORICAL_DEFAULT" in section
    assert "semantic_class=CURRENT_AUTHORITY" not in section
    doc = copy.deepcopy(_doc())
    for family in doc["parameter_families"]:
        if family["family_id"] == "historical_crs_limits_25_500":
            family["authority_status"] = "CURRENT_AUTHORITY"
    errors = MAP.validate_evidence(doc, REPO)
    assert any("historical default promoted to CURRENT" in error for error in errors)


def test_canonical_model_semantic_is_not_aged_into_historical() -> None:
    section = MAP.render_views(_doc())["parameter_lineage"].split(
        "## model_adverse_exit_distance_80", 1
    )[1]
    section = section.split("## ", 1)[0]
    assert "semantic_class=CANONICAL_MODEL_SEMANTIC" in section
    assert "historical_default_status=NOT_HISTORICAL_DEFAULT" in section
    doc = copy.deepcopy(_doc())
    for family in doc["parameter_families"]:
        if family["family_id"] == "model_adverse_exit_distance_80":
            family["historical_default_status"] = "HISTORICAL_DEFAULT"
    errors = MAP.validate_evidence(doc, REPO)
    assert any("model semantic aged into historical default" in error for error in errors)


def test_no_map_impact_without_change_bound_evidence_fails() -> None:
    declaration = {
        "authority_effect": "NONE",
        "selector_used_as_map_impact_authority": False,
        "verdict": "NO_MAP_IMPACT",
        "reason": "tooling only",
        "changed_paths": ["tests/ops/test_current_system_interaction_authority_map_v1.py"],
        "changed_paths_sha256": MAP.paths_sha256(
            ["tests/ops/test_current_system_interaction_authority_map_v1.py"]
        ),
        "evidence_refs": [],
        "covered_candidate_paths": [],
    }
    errors = MAP.evaluate_impact(
        declaration["changed_paths"],
        declaration,
        surfaces=[],
        surfaces_exhaustive=False,
        source_changed=False,
        derived_clean=True,
    )
    assert any("evidence missing" in error for error in errors)


def test_undeterminable_impact_fails_closed() -> None:
    changed = ["README.md"]
    declaration = {
        "authority_effect": "NONE",
        "selector_used_as_map_impact_authority": False,
        "verdict": "NO_MAP_IMPACT",
        "reason": "guess",
        "changed_paths": changed,
        "changed_paths_sha256": MAP.paths_sha256(changed),
        "evidence_refs": ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
        "covered_candidate_paths": [],
    }
    errors = MAP.evaluate_impact(
        changed,
        declaration,
        surfaces=["src/ops/full_core_live_path_composition_root_v1/"],
        surfaces_exhaustive=False,
        source_changed=False,
        derived_clean=True,
    )
    assert any("undeterminable impact" in error for error in errors)


def test_map_update_required_without_source_or_regen_fails() -> None:
    changed = ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"]
    declaration = {
        "authority_effect": "NONE",
        "selector_used_as_map_impact_authority": False,
        "verdict": "MAP_UPDATE_REQUIRED",
        "reason": "runbook pin moved",
        "changed_paths": changed,
        "changed_paths_sha256": MAP.paths_sha256(changed),
        "evidence_refs": ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
        "covered_candidate_paths": [],
    }
    errors = MAP.evaluate_impact(
        changed,
        declaration,
        surfaces=["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
        surfaces_exhaustive=False,
        source_changed=False,
        derived_clean=False,
    )
    assert any("without structured source update" in error for error in errors)
    assert any("without regenerated derived views" in error for error in errors)


def test_stale_or_missing_evidence_ref_fails() -> None:
    assert MAP.evidence_ref_status(REPO, "does/not/exist.py") == "MISSING"
    assert (
        MAP.evidence_ref_status(
            REPO,
            "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            expected_sha256="0" * 64,
        )
        == "STALE"
    )
    doc = copy.deepcopy(_doc())
    doc["domains"][0]["evidence_refs"] = ["missing/map/evidence.py"]
    errors = MAP.validate_evidence(doc, REPO)
    assert any("missing evidence ref missing/map/evidence.py" in error for error in errors)


def test_map_module_has_no_runtime_write_authority() -> None:
    assert MAP.validate_authority_none() == []
    assert MAP.AUTHORITY_EFFECT == "NONE"
    assert "selector" not in MAP.evaluate_impact.__code__.co_varnames


def test_existing_selector_files_unchanged() -> None:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "origin/main",
            "--",
            "scripts/ops/ci_test_selection_v1.py",
            "config/ci/file_category_mapping.yaml",
            ".github/workflows/ci.yml",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""


def test_normalize_unknown_to_current_rejected() -> None:
    doc = copy.deepcopy(_doc())
    doc["normalize_unknown_to_current"] = True
    errors = MAP.validate_schema(doc, MAP._load_json(MAP.SCHEMA_PATH))
    assert any("normalize_unknown_to_current" in error for error in errors)


@pytest.mark.parametrize(
    "family_id",
    [
        "historical_crs_limits_25_500",
        "historical_maximum_quantity_100",
        "historical_fixture_prices_3500_3400",
        "historical_equity_sentinel_10000",
    ],
)
def test_historical_families_remain_historical(family_id: str) -> None:
    families = {item["family_id"]: item for item in _doc()["parameter_families"]}
    assert families[family_id]["semantic_class"] == "HISTORICAL_DEFAULT"
    assert families[family_id]["authority_status"] != "CURRENT_AUTHORITY"
