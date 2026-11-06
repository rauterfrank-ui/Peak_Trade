"""Tests for V3.2 baseline-first lifecycle resolution v1 (composite binding, no new authority)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    CURRENT_MV2_DP_DECISION_SSOT,
    CURRENT_PRODUCTIVE_ENTRYPOINT,
    DECISION_CONFIG,
    EARLIEST_TRUE_REMAINING_GAP,
    EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2,
    INTEGRATED_REPLAY_CURRENT_ROLE,
    LAYERED_CORE_CURRENT_ROLE,
    NEW_BASELINE_GATE_RUNTIME_AUTHORITY,
    NORMATIVE_SPEC,
    P5_ADJUDICATION_LABEL,
    WORKPACKAGE_ID,
    AdjudicationVerdict,
    adjudicate_v32_baseline_first_requirements_v1,
    assert_no_new_baseline_gate_runtime_authority_v1,
    assert_replay_remains_decision_ssot_v1,
    composite_baseline_first_binding_v1,
    earliest_missing_edge_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    optimization_can_direct_write_runtime_seam_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1.constants_v1 import (
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    IndependentTradingDecisionAuthorityError,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
    deny_independent_trading_decision_authority_v1,
    IngressSurfaceClass,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTIVE_CYCLE_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def test_decision_config_aligns_with_binding() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    binding = composite_baseline_first_binding_v1(repo_root=REPO_ROOT)
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["normative_spec"] == NORMATIVE_SPEC
    assert decision["new_baseline_gate_runtime_authority"] is False
    assert decision["p5_authority_cutover_authorized"] is False
    assert decision["owner_decision_required_for_productive_cutover"] is False
    assert decision["expected_d24_verdict"] == "PROVEN_CURRENT"
    assert decision["expected_d25_verdict"] == "PROVEN_CURRENT"
    assert decision["expected_d26_verdict"] == "PROVEN_CURRENT"
    assert decision["current_mv2_dp_decision_ssot"] == CURRENT_MV2_DP_DECISION_SSOT
    assert binding["current_mv2_dp_decision_ssot"] == CURRENT_MV2_DP_DECISION_SSOT
    assert binding["current_productive_entrypoint"] == CURRENT_PRODUCTIVE_ENTRYPOINT
    assert binding["p5_adjudication"] == P5_ADJUDICATION_LABEL
    assert binding["layered_core_current_role"] == LAYERED_CORE_CURRENT_ROLE
    assert binding["integrated_replay_current_role"] == INTEGRATED_REPLAY_CURRENT_ROLE
    assert binding["optimization_universe_join_authorized"] is False


def test_d24_d25_d26_proven_d27_partial() -> None:
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    by_id = {r.requirement_id: r for r in rows}
    assert by_id["D24"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["D24"].earliest_missing_edge is None
    assert by_id["D25"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["D25"].earliest_missing_edge is None
    assert by_id["D26"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["D26"].earliest_missing_edge is None
    assert by_id["D27"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["D27"].earliest_missing_edge is None
    assert by_id["REQ-BL-SEQ-03"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert earliest_missing_edge_v1(rows) is None


def test_earliest_gap_not_cutover_related() -> None:
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    edge = earliest_missing_edge_v1(rows)
    if edge is None:
        assert all(r.verdict.value == "PROVEN_CURRENT" for r in rows if r.requirement_id == "D27")
        return
    assert "cutover" not in edge.lower()
    assert (
        edge
        in (
            EARLIEST_TRUE_REMAINING_GAP,
            EARLIEST_TRUE_REMAINING_GAP_AFTER_F1_F2,
        )
        or "lifecycle" in edge
        or "test_entry" in edge
    )


def test_replay_ssot_and_productive_entrypoint_unchanged() -> None:
    assert TRADING_DECISION_AUTHORITY_OWNER == CURRENT_MV2_DP_DECISION_SSOT
    assert P5_AUTHORITY_CUTOVER_AUTHORIZED is False
    assert PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is False
    assert_replay_remains_decision_ssot_v1()
    text = PRODUCTIVE_CYCLE_MODULE.read_text(encoding="utf-8")
    assert "run_integrated_offline_trading_logic_replay_v1" in text
    assert "run_current_productive_master_v2_runtime_cycle_v1" in text
    assert "run_p5_layered_core_authority_seam_v1" not in text


def test_layered_core_not_parallel_decision_writer_in_productive_cycle() -> None:
    text = PRODUCTIVE_CYCLE_MODULE.read_text(encoding="utf-8")
    assert "orchestrate_naked_layered_core_v1" not in text
    assert "prepare_productive_layered_core_replay_bind_v1" in text


def test_governed_return_and_mutation_invariants_proven() -> None:
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    by_id = {r.requirement_id: r for r in rows}
    assert by_id["REQ-BL-INV-03"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["REQ-BL-SEQ-05"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert OPTIMIZATION_CORE_MUTATION_AUTHORITY == "NONE"
    assert optimization_can_direct_write_runtime_seam_v1() is False


def test_optimization_cannot_claim_independent_trading_decision() -> None:
    with pytest.raises(IndependentTradingDecisionAuthorityError):
        deny_independent_trading_decision_authority_v1(
            surface_id="optimization_experiment_plane",
            surface_class=IngressSurfaceClass.OPTIMIZATION,
            claims_trading_decision_authority=True,
        )


def test_no_new_baseline_gate_runtime_authority() -> None:
    assert NEW_BASELINE_GATE_RUNTIME_AUTHORITY is False
    assert_no_new_baseline_gate_runtime_authority_v1()
