"""Static/read-only tests for Master V2 / Double Play P0 evidence-seam census."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p0_evidence_seam_census_v1 import (
    BLUEPRINT_BASELINE_SHA,
    SCHEMA_VERSION,
    WORKPACKAGE_ID,
    assert_p0_census_invariants_v1,
    run_master_v2_double_play_p0_evidence_seam_census_v1,
    write_p0_census_artifacts_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    LAYER_ORDER_V1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs/evidence/master_v2_double_play_evidence_input_plane_p0"
CENSUS_JSON = ARTIFACT_DIR / "l1_l10_evidence_seam_census_v1.json"


def test_p0_census_covers_exactly_l1_l10_with_evidence() -> None:
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    assert_p0_census_invariants_v1(census)
    assert census["schema_version"] == SCHEMA_VERSION
    assert census["workpackage_id"] == WORKPACKAGE_ID
    assert census["layer_count"] == 10
    assert len(census["census_layers"]) == len(LAYER_ORDER_V1)
    for row in census["census_layers"]:
        assert row["evidence_refs"]
        assert row["owner_evidence"] == "PROVEN_CURRENT"
        adm = row["external_evidence_admissibility"]
        assert adm in {
            "PROVEN_CURRENT",
            "PROVEN_CLOSED",
            "PROVEN_BOUNDED_TYPED_ONLY",
            "ABSENT",
            "CONFLICTING",
            "UNKNOWN",
        }
        assert (
            "external" not in adm.lower()
            or adm != "PROVEN_CURRENT"
            or row["layer_id"].startswith("L6")
        )


def test_no_blanket_external_evidence_permission() -> None:
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    for row in census["census_layers"]:
        if row["layer_id"] == "L6_DYNAMIC_SCOPE_GENERATOR":
            assert row["external_evidence_admissibility"] == "PROVEN_BOUNDED_TYPED_ONLY"
            continue
        assert row["external_evidence_admissibility"] in {"PROVEN_CLOSED", "ABSENT", "UNKNOWN"}


def test_no_ab_implementation_and_no_dp_semantic_mutation_claim() -> None:
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    assert census["component_a_implementation_detected"] is False
    assert census["component_b_implementation_detected"] is False
    assert census["dp_semantics_changed_by_this_wp"] is False
    assert census["cap_2_3_authority_changed_by_this_wp"] is False
    assert census["cap_2_4_authority_changed_by_this_wp"] is False
    assert census["crs_authority_changed_by_this_wp"] is False
    assert census["execution_authority_changed_by_this_wp"] is False
    assert census["external_effect_authority_changed_by_this_wp"] is False


def test_bypass_census_has_intelligence_to_layer_direct_call_proven_absent() -> None:
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    by_id = {e["path_id"]: e for e in census["direct_external_to_dp_bypass_census"]}
    assert (
        by_id["external_intelligent_producer_to_dp_layer_direct_call"]["classification"]
        == "PROVEN_ABSENT"
    )


def _json_normalized(obj: object) -> object:
    return json.loads(json.dumps(obj, sort_keys=True))


def test_committed_census_json_matches_runner() -> None:
    assert CENSUS_JSON.is_file(), "run write_p0_census_artifacts_v1 to refresh committed JSON"
    on_disk = json.loads(CENSUS_JSON.read_text(encoding="utf-8"))
    live = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    assert on_disk["layer_count"] == live["layer_count"]
    assert _json_normalized(live["census_layers"]) == on_disk["census_layers"]
    assert (
        _json_normalized(live["direct_external_to_dp_bypass_census"])
        == on_disk["direct_external_to_dp_bypass_census"]
    )


def test_write_artifacts_idempotent() -> None:
    write_p0_census_artifacts_v1(REPO_ROOT)
    assert (ARTIFACT_DIR / "p1_design_input_block_v1.json").is_file()
    assert (ARTIFACT_DIR / "open_conflict_register_v1.json").is_file()


def test_blueprint_baseline_sha_recorded() -> None:
    census = run_master_v2_double_play_p0_evidence_seam_census_v1(repo_root=REPO_ROOT)
    assert census["blueprint_baseline_sha"] == BLUEPRINT_BASELINE_SHA
