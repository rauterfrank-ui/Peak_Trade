"""GHV-referenced geometry evidence bridge + intelligence lineage closure v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.ghv_intelligence_lineage_completeness_v1 import (
    REALIZED_UNAVAILABLE,
    STRUCTURAL_COMPLETE,
    STRUCTURAL_PARTIAL,
    derive_realized_economic_completeness_v1,
    derive_structural_outcome_completeness_v1,
)
from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
    GHV_AUTHORITY,
    LineageSlotStatusV1,
    run_ghv_referenced_intelligence_superstructure_offline_cycle_v1,
)
from src.governance.ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1 import (
    load_ghv_reference_manifest_config_v1,
    prove_ghv_reference_artifacts_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_decision_time_geometry_evidence_v1 import (
    GEOMETRY_EVIDENCE_AUTHORITY,
    GHV_AUTHORITY as GEO_GHV_AUTHORITY,
    build_decision_time_geometry_evidence_v1_from_scope_trace_v1,
    geometry_evidence_immutable_digest_check_v1,
)
from tests.governance.test_ghv_referenced_complete_intelligence_superstructure_integration_v1 import (
    _offline_request,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GHV_ROOT = (
    REPO_ROOT / "evidence/research/ghv_referenced_full_system_natural_enter_pre_external_proof_v3/"
    "20261006T182600Z"
)
GHV_WITNESS = GHV_ROOT / "bounded_run_post_merge_t2_causal_reproof_001"
SCOPE_TRACE = GHV_WITNESS / "golden_happy_scope_decision_trace_v1.jsonl"
PENDING_INDEX = (
    GHV_ROOT / "fresh_lane_state_root/LANE_1/natural_enter_pending_outcome_index_v1.json"
)


def _enter_scope_trace_row() -> dict:
    for line in SCOPE_TRACE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("master_v2_decision_outcome") or "").lower() == "enter_long":
            return row
    raise AssertionError("enter_long scope trace missing")


def test_ghv_reference_manifest_deterministic() -> None:
    proof = prove_ghv_reference_artifacts_v1()
    assert proof["artifacts_ok"] is True
    assert proof["ghv_authority"] == "NONE"
    manifest = load_ghv_reference_manifest_config_v1()
    assert manifest["ghv_authority"] == "NONE"


def test_ghv_and_geometry_authority_none() -> None:
    assert GHV_AUTHORITY == "NONE"
    assert GEOMETRY_EVIDENCE_AUTHORITY == "NONE"
    assert GEO_GHV_AUTHORITY == "NONE"


def test_geometry_from_scope_trace_preserves_units_and_immutable() -> None:
    row = _enter_scope_trace_row()
    before_band = float(row["effective_hysteresis_band"])
    evidence = build_decision_time_geometry_evidence_v1_from_scope_trace_v1(row)
    assert float(evidence["effective_hysteresis_band"]) == before_band
    assert geometry_evidence_immutable_digest_check_v1(evidence) is True
    row["effective_hysteresis_band"] = 999.0
    assert float(evidence["effective_hysteresis_band"]) == before_band


def test_missing_geometry_values_remain_none_not_zero_fill() -> None:
    row = _enter_scope_trace_row()
    row = dict(row)
    row.pop("layer_c_reversal_distance", None)
    evidence = build_decision_time_geometry_evidence_v1_from_scope_trace_v1(row)
    assert evidence.get("layer_c_reversal_distance") is None


def test_structural_vs_realized_completeness_honest() -> None:
    partial = {
        "decision_event_ref": "ddo.dec:1",
        "source_learning_state_record_ref": "ls.1",
        "outcome_semantic_class": "OBSERVED_PRODUCTIVE_PRE_EXTERNAL",
        "actual_outcome_ref": "",
        "outcome_evidence_provenance": {"fill_source_type": "NO_FILL"},
    }
    assert derive_structural_outcome_completeness_v1(partial) == STRUCTURAL_PARTIAL
    assert derive_realized_economic_completeness_v1(partial) == REALIZED_UNAVAILABLE
    complete = {**partial, "actual_outcome_ref": "meas.1"}
    assert derive_structural_outcome_completeness_v1(complete) == STRUCTURAL_COMPLETE


def test_offline_cycle_no_ghost_economic_fields(tmp_path: Path) -> None:
    cycle = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
        _offline_request(tmp_path)
    )
    lineage = cycle["intelligence_lineage"]
    assert "economic_outcome_quality" not in lineage
    assert "cost_model_quality" not in lineage
    assert "structural_outcome_completeness" in lineage
    assert "realized_economic_completeness" in lineage


def test_offline_cycle_geometry_ref_from_evidence_source_refs(tmp_path: Path) -> None:
    from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
        GhvReferencedIntelligenceOfflineCycleRequestV1,
    )
    from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
        SURFACE_ID,
    )
    from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
        _plane_request,
    )

    req = _offline_request(tmp_path)
    le = dict(req.learning_evidence)
    req2 = GhvReferencedIntelligenceOfflineCycleRequestV1(
        learning_evidence=le,
        plane_request=_plane_request(le),
        optimization_surface_id=SURFACE_ID,
        replay_seed=3,
        geometry_evidence_ref="ghv.gev.abc123def4567890abc123def4567890abc123de",
    )
    out = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(req2)
    geo = out["intelligence_lineage"]["geometry_evidence_ref"]
    assert geo["status"] == LineageSlotStatusV1.PRESENT.value


def test_mina_pending_from_reference_evidence() -> None:
    pending = json.loads(PENDING_INDEX.read_text(encoding="utf-8"))
    rec = pending["records_by_decision_event_ref"]["ddo.dec:7b6a2f315833f9c3462b0e8d"]
    assert rec["pending_outcome_id"] == "neo.pending.ca567ad2099484912c1e643c973476c1"
    assert rec["bars_observed"] == 0
    assert rec["n_bars_required"] == 2
    assert rec["status"] == "PENDING"


def test_mina_ghv_report_checkpoints() -> None:
    report = json.loads(
        (GHV_WITNESS / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").read_text(encoding="utf-8")
    )
    assert str(report.get("NATURAL_ENTER_OBSERVED")).lower() == "true"
    assert str(report.get("PRE_EXTERNAL_REACHED")).lower() == "true"
    assert int(report.get("POST_COUNT", -1)) == 0
    assert int(report.get("EXTERNAL_EFFECT_COUNT", -1)) == 0
    assert report.get("NATIVE_ID") == "MINA-USDT-SWAP"


def test_lineage_slot_status_enum_includes_historical() -> None:
    assert LineageSlotStatusV1.HISTORICAL_REF_NOT_PRESENT.value == "HISTORICAL_REF_NOT_PRESENT"


def test_authority_constants_unchanged() -> None:
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    )
    from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
        PRODUCTIVE_ACTIVATION_AUTHORIZED,
    )
    from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
        AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
    )
    from src.governance.m10_promotion_boundary_v1 import (
        AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    )

    assert RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS == 600
    assert PRODUCTIVE_ACTIVATION_AUTHORIZED is False
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is False
