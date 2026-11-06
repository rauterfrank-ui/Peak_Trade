from __future__ import annotations

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    NO_AUTHORITY_FLAGS,
    build_trace_matrix,
)


def _inventory_fixture() -> dict:
    surfaces = []
    for surface_id in [
        "bull_bear_state_switch",
        "scope_adverse_exit_and_reversal_preparation",
        "flat_before_opposite_side",
        "entry_position_exit_policy",
        "capital_risk_sizing",
        "safety_kernel_and_killswitch_boundary",
        "reconciliation_unknown_outcome",
        "promotion_gate_boundary",
        "ai_observability_feedback_boundary",
        "double_play_composition",
        "survival_and_suitability",
        "canonical_order_intent_boundary",
    ]:
        surfaces.append(
            {
                "surface_id": surface_id,
                "required_status": f"{surface_id.upper()}_STATUS",
                "canonical_owner_candidates": [{"path": f"src/canonical/{surface_id}.py"}],
                "backtest_binding_candidates": [{"path": f"src/backtest/{surface_id}.py"}],
                "runtime_boundary_candidates": [{"path": f"src/runtime/{surface_id}.py"}],
            }
        )
    data = {
        "schema": "BacktestRuntimeDecisionParityInventoryV1",
        "inventory_surface_count": 12,
        "surfaces": surfaces,
    }
    data.update(NO_AUTHORITY_FLAGS)
    return data


def test_trace_matrix_has_12_edges_and_selects_trace_assertion_plan() -> None:
    matrix = build_trace_matrix(_inventory_fixture())
    assert matrix["schema"] == "BacktestRuntimeDecisionParityTraceMatrixV1"
    assert matrix["trace_edge_count"] == 12
    assert len(matrix["trace_edges"]) == 12
    assert matrix["next_unbound_node"] == "bull_bear_state_switch"
    assert matrix["chain_surface_binding_complete"] is False
    assert matrix["selected_next_rewire_plan"]["plan_type"] == "NARROW_TRACE_ASSERTION_FIRST"
    assert matrix["selected_next_rewire_plan"]["selected_surface_id"] == "bull_bear_state_switch"


def test_trace_matrix_makes_no_forbidden_claims() -> None:
    matrix = build_trace_matrix(_inventory_fixture())
    assert matrix["runtime_authority"] is False
    assert matrix["orders_allowed"] is False
    assert matrix["economic_claim"] is False
    assert matrix["full_canonical_chain_wired_claimed"] is False
    assert matrix["backtest_runtime_decision_parity_pass_claimed"] is False
    assert matrix["system_economic_evidence_admissible"] is False
    forbidden = matrix["selected_next_rewire_plan"]["forbidden_claims"]
    assert "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true" in forbidden
    assert "FULL_CANONICAL_CHAIN_WIRED=true" in forbidden


def test_all_edges_are_trace_candidates_not_pass_claims() -> None:
    matrix = build_trace_matrix(_inventory_fixture())
    states = {edge["trace_state"] for edge in matrix["trace_edges"]}
    assert states == {"TRACE_CANDIDATE_READY_NOT_ASSERTED"}
    for edge in matrix["trace_edges"]:
        assert edge["next_action"] == "add_narrow_trace_assertion_before_rewire"
        assert edge["canonical_candidate"] != "NONE_DISCOVERED"
        assert edge["backtest_candidate"] != "NONE_DISCOVERED"
        assert edge["runtime_boundary_candidate"] != "NONE_DISCOVERED"
