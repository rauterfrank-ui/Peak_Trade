"""GHV-referenced complete intelligence superstructure integration v1 — focused proofs."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as M9_SURFACE_ID,
)
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    P5_PRODUCER_BRIDGE_PERFORMED,
    SEARCH_EXECUTED,
)
from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
    CYCLE_STATUS_COMPLETE,
    GHV_AUTHORITY,
    GVEF_AUTHORITY,
    POST_ALLOWED,
    run_ghv_referenced_intelligence_superstructure_offline_cycle_v1,
    GhvReferencedIntelligenceOfflineCycleRequestV1,
)
from src.governance.ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1 import (
    prove_ghv_reference_artifacts_v1,
)
from src.governance.ghv_referenced_static_semantic_look_ahead_v1 import (
    run_ghv_referenced_static_semantic_look_ahead_v1,
)
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    M10PromotionState,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_intelligence_lineage_forensic_observability_v1 import (
    GHV_AUTHORITY as LINEAGE_GHV_AUTHORITY,
    build_intelligence_lineage_observability_record_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MV2_CYCLE_PATH = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_runtime_cycle_v1.py"
)
LINEAGE_OBS_PATH = (
    REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/"
    "ghv_intelligence_lineage_forensic_observability_v1.py"
)


def _offline_request(tmp_path: Path) -> GhvReferencedIntelligenceOfflineCycleRequestV1:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    return GhvReferencedIntelligenceOfflineCycleRequestV1(
        learning_evidence=evidence,
        plane_request=_plane_request(evidence),
        optimization_surface_id=M9_SURFACE_ID,
        parameter_config_delta={"max_age_seconds": 600},
        replay_seed=3,
    )


def test_ghv_reference_artifacts_and_manifest_prove(tmp_path: Path) -> None:
    proof = prove_ghv_reference_artifacts_v1()
    assert proof["ghv_authority"] == "NONE"
    assert proof["artifacts_ok"] is True
    assert proof["missing_artifacts"] == ()


def test_offline_cycle_composes_m4_m8_through_m10_hard_stop(tmp_path: Path) -> None:
    first = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
        _offline_request(tmp_path)
    )
    second = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
        _offline_request(tmp_path)
    )
    assert first["status"] == CYCLE_STATUS_COMPLETE
    assert first["result_digest"] == second["result_digest"]
    assert first["ghv_authority"] == "NONE"
    assert first["gvef_authority"] == "NONE"
    assert first["post_allowed"] is False
    assert first["productive_config_mutation_performed"] is False
    assert first["m10_promotion_state"] == M10PromotionState.VALIDATED.value
    lineage = first["intelligence_lineage"]
    assert lineage["m10_hard_stop"] is True
    assert lineage["mi_ref"]["status"] == "INTENTIONALLY_DISCONNECTED"
    gvef = first["gvef_reproof"]
    assert gvef["gvef_authority"] == "NONE"
    assert gvef["reproof_pass"] is True


def test_offline_cycle_forbids_search_and_p5_bridge_constants() -> None:
    assert SEARCH_EXECUTED is False
    assert P5_PRODUCER_BRIDGE_PERFORMED is False


def test_static_semantic_look_ahead_no_productive_divergence() -> None:
    la = run_ghv_referenced_static_semantic_look_ahead_v1()
    assert la["ghv_authority"] == "NONE"
    assert la["productive_first_causal_divergence"] == "NONE"
    assert la["intelligence_first_causal_divergence"] == "NONE"


def test_boundary_invariants_unchanged() -> None:
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert PRODUCTIVE_ACTIVATION_AUTHORIZED is False
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is False
    assert GHV_AUTHORITY == "NONE"
    assert GVEF_AUTHORITY == "NONE"
    assert POST_ALLOWED is False
    assert LINEAGE_GHV_AUTHORITY == "NONE"


def test_mv2_cycle_does_not_import_offline_orchestrator() -> None:
    tree = ast.parse(MV2_CYCLE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden = (
        "src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1"
    )
    assert forbidden not in imports
    assert "ghv_intelligence_lineage_forensic_observability_v1" in MV2_CYCLE_PATH.read_text()


class _ReplayStub:
    replay_pass = True
    evidence = type("E", (), {"decision_outcome": "enter_long"})()


def test_intelligence_lineage_record_refs_only_no_authority_fields() -> None:
    replay = _ReplayStub()
    record = build_intelligence_lineage_observability_record_v1(
        cycle_id="cycle:1",
        instrument_id="MINA-USDT-SWAP",
        venue_native_id="MINA-USDT-SWAP",
        ddo_capture_summary={"ok": True, "record_ids": ["ddo.dec:abc"]},
        ddo_offline_export_handoff={
            "ok": True,
            "decision_event_ref": "ddo.dec:abc",
            "learning_state_record_ref": "ddo.ls:1",
            "learning_evidence_record_id": "ddo.le:1",
            "optimization_ack_status": "ACCEPTED",
        },
        replay=replay,
    )
    assert record["ghv_authority"] == "NONE"
    assert record["decision_unchanged"] is True
    assert record["capture_failure_changes_decision"] is False
    assert record["experiment_ref"]["status"] == "NOT_REACHED"
    assert record["m10_ref"]["status"] == "NOT_REACHED"
    assert "trading_authority" not in record


@pytest.mark.parametrize(
    "slot",
    [
        "decision_event_ref",
        "learning_evidence_ref",
        "mi_ref",
        "m10_ref",
    ],
)
def test_lineage_slots_explicit_status(slot: str) -> None:
    replay = _ReplayStub()
    record = build_intelligence_lineage_observability_record_v1(
        cycle_id="c",
        instrument_id="i",
        venue_native_id="i",
        ddo_capture_summary=None,
        ddo_offline_export_handoff=None,
        replay=replay,
    )
    assert "status" in record[slot]
    assert "ref" in record[slot]


def test_wp_invariant_matrix_productive_and_intelligence_boundaries(
    tmp_path: Path,
) -> None:
    """Consolidated proofs for WP §23 checklist (bounded; no productive mutation)."""
    from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
        OPTIMIZATION_PRODUCTIVE_AUTHORITY,
    )
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
    )
    from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
        DDO_TRADING_AUTHORITY,
        EIP_ACTIVATION_PERFORMED,
        EXTERNAL_EFFECT_AUTHORIZED,
        SUPERVISOR_ACTIVATION_PERFORMED,
    )

    cycle = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
        _offline_request(tmp_path)
    )
    assert OPTIMIZATION_PRODUCTIVE_AUTHORITY == "NONE"
    assert DDO_TRADING_AUTHORITY == "NONE"
    assert EIP_ACTIVATION_PERFORMED is False
    assert SUPERVISOR_ACTIVATION_PERFORMED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS == 600
    assert cycle["eip_activation_performed"] is False
    assert cycle["supervisor_activation_performed"] is False
    m4 = cycle["m4_m8_loop"]
    assert m4["trading_selection_effect"] == "NONE"
    assert m4["learning_state_mutation_performed"] is False
    assert m4["meta_evidence_authority"] == "NONE"
